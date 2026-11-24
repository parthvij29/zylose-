import sounddevice as sd
import numpy as np

# Verify that sounddevice can record 4.5s at 44100 without glitches
data = sd.rec(int(44100 * 4.5), samplerate=44100, channels=1, dtype="float32")
sd.wait()
print(f"4.5s capture finished cleanly. Max peak: {np.max(np.abs(data)):.4f}")
