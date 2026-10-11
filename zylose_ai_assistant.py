#!/usr/bin/env python3
"""
Zylose Conversational AI Assistant & Edge USB Bridge
-----------------------------------------------------
Architecture:
  1. Edge Hardware (ESP32): TinyML wake-word "Zylose" detection.
  2. USB Bridge (PC): Listens for ESP32 triggers on COM6, posts telemetry to Dashboard.
  3. Conversational AI Brain:
     - On wake-word, records user's voice question via PC microphone.
     - Performs Speech-to-Text (STT).
     - Generates concise response using GenAI (Gemini / Instant AI).
     - Speaks response aloud through laptop speakers (TTS).
     - Sends answer back to ESP32 over USB.
"""

import os
import sys
import time
import re
import io
import wave
import threading
import requests
import serial
import serial.tools.list_ports
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3

DASHBOARD_API = "http://localhost:3000/api/events"
DEVICE_ID = "ZYLOSE-ESP32-01"
BAUD_RATE = 115200
SAMPLE_RATE = 16000
LISTEN_DURATION = 4.5  # seconds to listen after wake-word

# Load Gemini API key if present
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_KEY and os.path.exists("Zylose-Dashboard/.env.local"):
    try:
        with open("Zylose-Dashboard/.env.local", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    GEMINI_KEY = line.split("=", 1)[1].strip()
    except Exception:
        pass

# Initialize TTS engine
tts_lock = threading.Lock()
try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty("rate", 175)  # Natural speaking speed
except Exception as e:
    tts_engine = None
    print(f"[Warning] TTS initialization: {e}")

def speak(text):
    """Speak text through PC speakers."""
    if not tts_engine:
        return
    with tts_lock:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"[TTS Error] {e}")

def find_esp32_port():
    """Auto-detect the ESP32 CP210x or CH340 COM port."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        if "cp210" in desc or "ch340" in desc or "silicon labs" in desc:
            return port.device
    return "COM6"

def post_event(result, confidence, unknown_score=0.0, silence_score=0.0):
    """Post an inference event to the Zylose Dashboard."""
    payload = {
        "device_id": DEVICE_ID,
        "result": result,
        "confidence": round(float(confidence), 4),
        "unknown_score": round(float(unknown_score), 4),
        "silence_score": round(float(silence_score), 4),
    }
    try:
        requests.post(DASHBOARD_API, json=payload, timeout=2)
    except Exception:
        pass

def query_ai(question):
    """Get concise intelligent answer using Gemini or Knowledge Search."""
    if GEMINI_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_KEY)
            prompt = (
                "You are Zylose, an intelligent edge voice assistant. "
                "Answer this question concisely in at most 1 or 2 clear sentences: "
                + question
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini API fallback] {e}")

    # Built-in instant answer fallback
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(question + " answer definition", max_results=1)
        if results and "body" in results[0]:
            body = results[0]["body"]
            sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 10]
            if sentences:
                return sentences[0] + "."
    except Exception:
        pass

    return f"I heard: {question}. Zylose is ready for your next command."

def record_and_process_voice(ser):
    """Record user question from microphone, transcribe, and speak answer."""
    print("\n" + "=" * 55)
    print(">>> [ZYLOSE LISTENING] Speak your question now...")
    print("=" * 55, flush=True)

    # Audio cue
    speak("Yes?")

    # Record audio from laptop microphone
    try:
        audio_data = sd.rec(
            int(LISTEN_DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16"
        )
        sd.wait()

        # Convert to WAV bytes in memory
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        wav_io.seek(0)

        # Transcribe using SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            recorded_audio = recognizer.record(source)

        print("[Transcribing speech...]", flush=True)
        user_query = recognizer.recognize_google(recorded_audio)
        print(f"\n[You asked]: \"{user_query}\"", flush=True)

        # Query AI brain
        print("[Generating AI response...]", flush=True)
        answer = query_ai(user_query)
        print(f"[Zylose Answer]: {answer}\n", flush=True)

        # Send response summary back over USB serial to ESP32
        try:
            ser.write(f"ANS:{answer[:50]}\n".encode("utf-8"))
        except Exception:
            pass

        # Speak answer aloud through laptop speaker
        speak(answer)

    except sr.UnknownValueError:
        print("[No speech detected or unclear audio]", flush=True)
        speak("I did not catch that.")
    except Exception as e:
        print(f"[Voice processing error] {e}", flush=True)

def main():
    port = find_esp32_port()
    print("=" * 65)
    print(" ZYLOSE CONVERSATIONAL VOICE ASSISTANT (EDGE + AI BRIDGE)")
    print(f" * Hardware Port   : {port} @ {BAUD_RATE} baud")
    print(f" * Dashboard Target: {DASHBOARD_API}")
    print(f" * AI Brain        : {'Gemini API' if GEMINI_KEY else 'Instant Knowledge Engine'}")
    print("=" * 65)
    print("Say 'Zylose' to activate your assistant!\n", flush=True)

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(1)
        ser.reset_input_buffer()
        print(f"[Connected] ESP32 listening on {port}...\n", flush=True)
    except Exception as e:
        print(f"[Error] Failed to open {port}: {e}")
        sys.exit(1)

    zylose_score = 0.0
    unknown_score = 0.0
    silence_score = 0.99
    last_silence_time = 0

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            # Parse inference scores
            if "Zylose score" in line and ":" in line:
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

            # Detection events
            if "ZYLOSE ACTIVATED" in line:
                print("\n" + "*" * 55, flush=True)
                print("*** [WAKE WORD DETECTED] ZYLOSE ACTIVATED! ***", flush=True)
                print("*" * 55, flush=True)
                post_event("zylose", max(zylose_score, 0.95), unknown_score, silence_score)
                # Handle full conversation
                record_and_process_voice(ser)

            elif "UNKNOWN DETECTED" in line:
                post_event("unknown", max(unknown_score, 0.70), unknown_score, silence_score)

            elif "SILENCE DETECTED" in line:
                now = time.time()
                if now - last_silence_time >= 3.0:
                    post_event("silence", max(silence_score, 0.95), unknown_score, silence_score)
                    last_silence_time = now

    except KeyboardInterrupt:
        print("\nAssistant stopped.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
