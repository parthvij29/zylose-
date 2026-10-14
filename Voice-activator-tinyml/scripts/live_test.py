#!/usr/bin/env python3
"""
Live voice test: records from mic, runs inference, shows result.
Rejects similar-sounding words using confidence margin.
"""

import sys
import time
import numpy as np
import sounddevice as sd
import tensorflow as tf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    MODELS_DIR, SAMPLE_RATE, AUDIO_SAMPLES, FEATURE_CONFIG,
    EXPECTED_FRAMES, NUM_MFCC, CLASS_LABELS, N_FFT, HOP_LENGTH
)
import librosa

WAKE_CLASSES = ("zylose", "hey_zylose")
CONFIDENCE_THRESHOLD = 0.70
MARGIN_THRESHOLD = 0.30


def record(duration=2.0):
    print(f"\nRecording in 3...")
    time.sleep(1)
    print(f"2...")
    time.sleep(1)
    print(f"1...")
    time.sleep(1)
    print("SPEAK NOW!\n")

    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()


def extract_features(audio):
    if len(audio) > AUDIO_SAMPLES:
        audio = audio[:AUDIO_SAMPLES]
    elif len(audio) < AUDIO_SAMPLES:
        audio = np.pad(audio, (0, AUDIO_SAMPLES - len(audio)))

    mfcc = librosa.feature.mfcc(
        y=audio.astype(np.float32), sr=SAMPLE_RATE,
        n_mfcc=NUM_MFCC, n_fft=N_FFT, hop_length=HOP_LENGTH,
        n_mels=FEATURE_CONFIG.num_mel_bins, fmin=0, fmax=SAMPLE_RATE // 2
    ).T

    if mfcc.shape[0] > EXPECTED_FRAMES:
        mfcc = mfcc[:EXPECTED_FRAMES]
    elif mfcc.shape[0] < EXPECTED_FRAMES:
        mfcc = np.pad(mfcc, ((0, EXPECTED_FRAMES - mfcc.shape[0]), (0, 0)))

    mean = np.mean(mfcc, axis=0, keepdims=True)
    std = np.std(mfcc, axis=0, keepdims=True) + 1e-8
    mfcc = (mfcc - mean) / std

    return mfcc.astype(np.float32)[np.newaxis, ..., np.newaxis]


def check_wake_word(probs):
    """Check if wake word detected with sufficient confidence and margin."""
    pred_idx = np.argmax(probs)
    pred_class = CLASS_LABELS[pred_idx]
    confidence = probs[pred_idx]

    if pred_class not in WAKE_CLASSES:
        return False, pred_class, confidence, "not a wake word class"

    if confidence < CONFIDENCE_THRESHOLD:
        return False, pred_class, confidence, f"confidence {confidence:.0%} < {CONFIDENCE_THRESHOLD:.0%}"

    sorted_probs = np.sort(probs)[::-1]
    margin = sorted_probs[0] - sorted_probs[1]
    if margin < MARGIN_THRESHOLD:
        return False, pred_class, confidence, f"margin {margin:.2f} < {MARGIN_THRESHOLD:.2f} (too close to other class)"

    return True, pred_class, confidence, "passed"


def main():
    model_path = MODELS_DIR / "zylose_kws.keras"
    if not model_path.exists():
        print("Model not found. Train first with: python scripts/train.py")
        return

    model = tf.keras.models.load_model(model_path)

    print("=" * 40)
    print("  ZYLOSE WAKE WORD TEST")
    print("=" * 40)
    print(f"  Threshold: {CONFIDENCE_THRESHOLD:.0%}")
    print(f"  Margin:    {MARGIN_THRESHOLD:.2f}")
    print("  Say 'Zylose' or anything else.\n")

    while True:
        input("Press ENTER to record (or Ctrl+C to quit)...")
        try:
            audio = record(duration=2.0)
        except KeyboardInterrupt:
            print("\nDone.")
            break

        features = extract_features(audio)
        probs = model.predict(features, verbose=0)[0]

        detected, pred_class, confidence, reason = check_wake_word(probs)

        print("-" * 40)
        for i, cls in enumerate(CLASS_LABELS):
            bar = "#" * int(probs[i] * 30)
            marker = " *" if cls in WAKE_CLASSES else "  "
            print(f"  {cls:<12} {probs[i]:.2f} {bar}{marker}")
        print("-" * 40)

        sorted_probs = np.sort(probs)[::-1]
        margin = sorted_probs[0] - sorted_probs[1]

        if detected:
            print(f"\n  >>> WAKE WORD DETECTED: '{pred_class}' ({confidence:.0%}, margin: {margin:.2f}) <<<\n")
        else:
            print(f"\n  Result: {pred_class} ({confidence:.0%}) - REJECTED ({reason})\n")


if __name__ == "__main__":
    main()