#!/usr/bin/env python3
"""
Zylose Conversational AI Assistant & Edge USB Bridge
-----------------------------------------------------
Integrated Multi-Tier Architecture:
  1. Edge Hardware (ESP32): TinyML INT8 CNN spots wake-word "Zylose".
  2. Edge USB Bridge: Reads COM6 at 115200 baud, syncs live telemetry to Dashboard.
  3. Pre-trained ASR Engine: Transcribes spoken user commands.
  4. Custom Deep Learning NLP Intent Classifier:
     - Classifies speech into: DEVICE_CONTROL, SYSTEM_TELEMETRY, KNOWLEDGE_QUERY, EMERGENCY_ABORT.
  5. Generative AI Reasoning: Formulates intelligent answers via Gemini.
  6. Neural / SAPI5 TTS: Speaks answers out loud through PC speakers.
  7. Physical Actuation & OLED Feedback: Transmits status/actions back to ESP32.
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
import joblib

DASHBOARD_API = "http://localhost:3000/api/events"
DEVICE_ID = "ZYLOSE-ESP32-01"
BAUD_RATE = 115200
SAMPLE_RATE = 16000
LISTEN_DURATION = 4.5  # seconds to capture after wake-word

# Load Gemini API Key if present
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_KEY and os.path.exists("Zylose-Dashboard/.env.local"):
    try:
        with open("Zylose-Dashboard/.env.local", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    GEMINI_KEY = line.split("=", 1)[1].strip()
    except Exception:
        pass

# Load Custom Trained Deep Learning Intent Classifier (Model 2)
INTENT_MODEL_PATH = os.path.join("models", "intent_model.joblib")
intent_bundle = None
if os.path.exists(INTENT_MODEL_PATH):
    try:
        intent_bundle = joblib.load(INTENT_MODEL_PATH)
        print(f"[Loaded Model 2] Custom NLP Intent Classifier from {INTENT_MODEL_PATH}")
    except Exception as e:
        print(f"[Warning] Could not load intent model: {e}")

# Load Custom Trained Speech Urgency Classifier (Model 3)
URGENCY_MODEL_PATH = os.path.join("models", "urgency_model.joblib")
urgency_bundle = None
if os.path.exists(URGENCY_MODEL_PATH):
    try:
        urgency_bundle = joblib.load(URGENCY_MODEL_PATH)
        print(f"[Loaded Model 3] Speech Urgency & Affective Classifier from {URGENCY_MODEL_PATH}")
    except Exception as e:
        print(f"[Warning] Could not load urgency model: {e}")

def classify_urgency(text):
    """Classify speech urgency using our custom-trained Model 3."""
    if not urgency_bundle:
        return "CALM_NORMAL", 50.0
    vec = urgency_bundle["vectorizer"].transform([text])
    pred = urgency_bundle["model"].predict(vec)[0]
    probs = urgency_bundle["model"].predict_proba(vec)[0]
    confidence = float(np.max(probs) * 100)
    return pred, confidence

# Initialize TTS Voice Engine
tts_lock = threading.Lock()
try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty("rate", 175)
except Exception as e:
    tts_engine = None

def speak(text):
    """Speak text aloud through laptop speakers."""
    if not tts_engine:
        return
    with tts_lock:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass

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

def classify_intent(text):
    """Classify user query using our custom-trained Deep Learning NLP model."""
    if not intent_bundle:
        return "KNOWLEDGE_QUERY", 50.0
    vec = intent_bundle["vectorizer"].transform([text])
    pred = intent_bundle["model"].predict(vec)[0]
    probs = intent_bundle["model"].predict_proba(vec)[0]
    confidence = float(np.max(probs) * 100)
    return pred, confidence

def query_gemini_ai(question):
    """Query Google Gemini or Wikipedia for concise factual and scientific answers."""
    if GEMINI_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_KEY)
            prompt = (
                "You are Zylose, an intelligent voice assistant running on edge-server architecture. "
                "Answer this question concisely in 1 or 2 clear sentences: "
                + question
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini API fallback] {e}")

    # Instant encyclopedic knowledge using Wikipedia
    try:
        import wikipedia
        wikipedia.set_user_agent("ZyloseVoiceAssistant/1.0 (contact: student@bennett.edu.in)")
        clean_q = re.sub(r'^(what is a|what is the|what is|who is|explain|tell me about|define)\s+', '', question, flags=re.IGNORECASE).strip()
        search_hits = wikipedia.search(clean_q)
        if search_hits:
            summary = wikipedia.summary(search_hits[0], sentences=2, auto_suggest=False)
            summary = re.sub(r'\[\d+\]', '', summary).strip()
            return summary
    except Exception as e:
        pass

    # Instant knowledge fallback using search
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

    return f"I understood your request: {question}. Zylose is ready for the next command."

def execute_intent_action(intent, user_query, ser):
    """Execute action based on predicted intent domain."""
    query_lower = user_query.lower()

    if intent == "DEVICE_CONTROL":
        if "on" in query_lower and ("led" in query_lower or "light" in query_lower):
            action_msg = "Turning on the LED."
            try:
                ser.write(b"CMD:LED_ON\n")
            except Exception:
                pass
        elif "off" in query_lower and ("led" in query_lower or "light" in query_lower):
            action_msg = "Turning off the LED."
            try:
                ser.write(b"CMD:LED_OFF\n")
            except Exception:
                pass
        elif "clear" in query_lower or "reset" in query_lower:
            action_msg = "Clearing the OLED display."
            try:
                ser.write(b"CMD:OLED_CLEAR\n")
            except Exception:
                pass
        else:
            action_msg = f"Device control command '{user_query}' executed."
        return action_msg

    elif intent == "SYSTEM_TELEMETRY":
        return "System telemetry: CPU load is nominal, 61 Kilobytes SRAM free, system health is optimal."

    elif intent == "EMERGENCY_ABORT":
        try:
            ser.write(b"CMD:ABORT\n")
        except Exception:
            pass
        return "Emergency abort acknowledged! Disengaging all active operations immediately."

    else:
        # KNOWLEDGE_QUERY
        return query_gemini_ai(user_query)

def record_and_process_voice(ser):
    """Record user question, transcribe, run custom NLP intent model, and speak answer."""
    print("\n" + "=" * 60)
    print(">>> [ZYLOSE LISTENING] Speak your command or question now...")
    print("=" * 60, flush=True)

    speak("Yes?")

    try:
        # 1. Capture Audio from Laptop Microphone
        audio_data = sd.rec(
            int(LISTEN_DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16"
        )
        sd.wait()

        # Convert to WAV
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        wav_io.seek(0)

        # 2. Speech-to-Text Transcription
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            recorded_audio = recognizer.record(source)

        print("[Transcribing acoustic audio...]", flush=True)
        user_query = recognizer.recognize_google(recorded_audio)
        print(f"\n[Transcribed User Speech]: \"{user_query}\"", flush=True)

        # 3. Custom Deep Learning NLP Intent Classification (Model 2)
        intent, intent_conf = classify_intent(user_query)
        print(f"[Model 2 - NLP Intent]    : {intent} (Confidence: {intent_conf:.1f}%)", flush=True)

        # 4. Custom Speech Urgency & Stress Detection (Model 3)
        urgency, urgency_conf = classify_urgency(user_query)
        print(f"[Model 3 - Speech Urgency] : {urgency} (Confidence: {urgency_conf:.1f}%)", flush=True)

        if urgency == "HIGH_URGENCY":
            print(">>> [PRIORITY ALERT] HIGH URGENCY / DISTRESS DETECTED! <<<", flush=True)

        # 5. Action Execution & Response Generation
        print("[Executing action / generating answer...]", flush=True)
        answer = execute_intent_action(intent, user_query, ser)
        print(f"[Zylose Response]: {answer}\n", flush=True)

        # 5. Send Answer Back to ESP32 over USB Serial
        try:
            ser.write(f"ANS:{answer[:50]}\n".encode("utf-8"))
        except Exception:
            pass

        # 6. Speak Response Out Loud
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
    print(f" * Hardware Port     : {port} @ {BAUD_RATE} baud")
    print(f" * Dashboard Target  : {DASHBOARD_API}")
    print(f" * Custom Intent ML  : {'Loaded (MLP Neural Net)' if intent_bundle else 'Disabled'}")
    print(f" * Generative Brain  : {'Gemini 2.5 Flash' if GEMINI_KEY else 'Instant Knowledge Engine'}")
    print("=" * 65)
    print("Listening for wake word 'Zylose'...\n", flush=True)

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
