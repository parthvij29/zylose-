import sounddevice as sd
import numpy as np
import speech_recognition as sr
import io
import wave

print("Say a question right now into the mic (e.g., 'what is today's date')...")
data = sd.rec(int(44100 * 3.5), samplerate=44100, channels=1, dtype="float32")
sd.wait()

raw_peak = float(np.max(np.abs(data)))
print(f"Recorded 3.5s. Raw peak: {raw_peak:.4f}")

# Boost audio with gain
if raw_peak > 0.0005:
    gain = min(0.9 / raw_peak, 60.0)
    boosted = data * gain
else:
    boosted = data
    gain = 1.0

int16_data = (np.clip(boosted, -1.0, 1.0) * 32767).astype(np.int16)

wav_io = io.BytesIO()
with wave.open(wav_io, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(44100)
    wf.writeframes(int16_data.tobytes())
wav_io.seek(0)

recognizer = sr.Recognizer()
with sr.AudioFile(wav_io) as source:
    audio = recognizer.record(source)

try:
    # Get detailed response
    res = recognizer.recognize_google(audio, show_all=True)
    print("Google STT Full Result:", res)
except Exception as e:
    print("Recognition error:", e)
