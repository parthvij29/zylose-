"""
DIAGNOSTIC: Records exactly what happens after "Yes?" is spoken.
Run this, then when you see RECORDING... say your question clearly.
"""
import sounddevice as sd
import numpy as np
import io, wave, time
import speech_recognition as sr

SAMPLE_RATE = 44100

def record_and_transcribe(label, duration):
    print(f"\n>>> [{label}] RECORDING for {duration}s... SPEAK NOW! <<<")
    data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    
    raw_peak = float(np.max(np.abs(data)))
    print(f"    Raw peak: {raw_peak:.6f}")
    
    if raw_peak > 0.00005:
        gain = min(0.85 / raw_peak, 80.0)
        data = data * gain
        print(f"    Gain applied: {gain:.1f}x  -> new peak: {float(np.max(np.abs(data))):.4f}")
    
    int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int16.tobytes())
    wav_io.seek(0)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio = recognizer.record(source)
    
    try:
        result = recognizer.recognize_google(audio, show_all=True)
        print(f"    Google Raw Result: {result}")
        if result and "alternative" in result:
            best = result["alternative"][0]["transcript"]
            print(f"    >> RECOGNIZED: '{best}'")
        else:
            print(f"    >> NO SPEECH RECOGNIZED (empty result)")
    except sr.UnknownValueError:
        print(f"    >> COULD NOT UNDERSTAND AUDIO")
    except Exception as e:
        print(f"    >> ERROR: {e}")

# --- Simulate what happens after "Zylose" detected ---
print("=== ZYLOSE DIAGNOSTIC TEST ===")
print("Step 1: Simulating 'Yes?' pause (1 second silence)...")
time.sleep(1.0)

print("\nStep 2: Now say your QUESTION (e.g., 'what is today date')...")
record_and_transcribe("QUESTION WINDOW", 4.5)
