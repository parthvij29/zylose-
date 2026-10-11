#!/usr/bin/env python3
"""
Zylose USB Serial Bridge
Bridges the ESP32 (via USB COM port) directly to the Zylose Dashboard and AI pipeline.
No Wi-Fi needed on the ESP32!
"""

import sys
import time
import re
import requests
import serial
import serial.tools.list_ports

DASHBOARD_API = "http://localhost:3000/api/events"
DEVICE_ID = "ZYLOSE-ESP32-01"
BAUD_RATE = 115200

def find_esp32_port():
    """Auto-detect the ESP32 CP210x or CH340 COM port."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        if "cp210" in desc or "ch340" in desc or "silicon labs" in desc:
            return port.device
    # Default fallback
    return "COM6"

def post_event(result, confidence, unknown_score, silence_score):
    """Post an inference event to the local Zylose Dashboard."""
    payload = {
        "device_id": DEVICE_ID,
        "result": result,
        "confidence": round(float(confidence), 4),
        "unknown_score": round(float(unknown_score), 4),
        "silence_score": round(float(silence_score), 4),
    }
    try:
        res = requests.post(DASHBOARD_API, json=payload, timeout=2)
        if res.status_code in (200, 201):
            print(f"[Dashboard Update] -> {result.upper()} (conf: {confidence:.2f})")
        else:
            print(f"[Dashboard Error] HTTP {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[Dashboard Sync Warning] Could not reach dashboard: {e}")

def main():
    port = find_esp32_port()
    print("=" * 60)
    print(f" ZYLOSE EDGE USB BRIDGE: Connecting to {port} @ {BAUD_RATE} baud")
    print(f" Dashboard target: {DASHBOARD_API}")
    print("=" * 60)

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(1)
        ser.reset_input_buffer()
        print(f"[Connected] Listening for live inferences from ESP32 on {port}...\n")
    except Exception as e:
        print(f"[Error] Failed to open {port}: {e}")
        sys.exit(1)

    curr_result = "silence"
    zylose_score = 0.0
    unknown_score = 0.0
    silence_score = 0.99
    last_silence_time = 0

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            # Check for score lines from log_current_inference
            if "Result" in line and ":" in line:
                match = re.search(r"Result\s*:\s*(\w+)", line)
                if match:
                    curr_result = match.group(1).lower()

            elif "Zylose score" in line and ":" in line:
                match = re.search(r"Zylose score\s*:\s*([\d\.]+)", line)
                if match:
                    zylose_score = float(match.group(1))

            elif "Unknown score" in line and ":" in line:
                match = re.search(r"Unknown score\s*:\s*([\d\.]+)", line)
                if match:
                    unknown_score = float(match.group(1))

            elif "Silence score" in line and ":" in line:
                match = re.search(r"Silence score\s*:\s*([\d\.]+)", line)
                if match:
                    silence_score = float(match.group(1))

            # Trigger detection blocks
            if "ZYLOSE ACTIVATED" in line:
                print("\n" + "*" * 50, flush=True)
                print(">>> [WAKE WORD TRIGGER] ZYLOSE ACTIVATED! <<<", flush=True)
                print("*" * 50, flush=True)
                conf = max(zylose_score, 0.90)
                post_event("zylose", conf, unknown_score, silence_score)

            elif "UNKNOWN DETECTED" in line:
                conf = max(unknown_score, 0.70)
                post_event("unknown", conf, unknown_score, silence_score)

            elif "SILENCE DETECTED" in line:
                now = time.time()
                # Post silence periodically so dashboard updates live
                if now - last_silence_time >= 3:
                    conf = max(silence_score, 0.95)
                    post_event("silence", conf, unknown_score, silence_score)
                    last_silence_time = now

    except KeyboardInterrupt:
        print("\nStopping USB bridge...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
