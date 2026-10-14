#!/usr/bin/env python3
"""
Test inference script: run inference on a single WAV file using Keras and TFLite models.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import tensorflow as tf

from config import (
    MODELS_DIR, SAMPLE_RATE, AUDIO_SAMPLES, FEATURE_CONFIG,
    EXPECTED_FRAMES, NUM_MFCC, CLASS_LABELS, CLASS_TO_IDX,
    N_FFT, HOP_LENGTH
)


def load_audio(filepath: Path) -> np.ndarray:
    """Load and preprocess audio file."""
    audio, sr = sf.read(str(filepath))
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    if sr != SAMPLE_RATE:
        audio = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=SAMPLE_RATE)
    return audio


def fix_audio_length(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Pad or trim audio to target length."""
    if len(audio) > target_samples:
        return audio[:target_samples]
    elif len(audio) < target_samples:
        pad = np.zeros(target_samples - len(audio), dtype=audio.dtype)
        return np.concatenate([audio, pad])
    return audio


def compute_mfcc(audio: np.ndarray) -> np.ndarray:
    """Compute MFCC features matching training config."""
    mfcc = librosa.feature.mfcc(
        y=audio.astype(np.float32),
        sr=SAMPLE_RATE,
        n_mfcc=NUM_MFCC,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=FEATURE_CONFIG.num_mel_bins,
        fmin=0,
        fmax=SAMPLE_RATE // 2
    )
    return mfcc.T


def normalize_features(features: np.ndarray) -> np.ndarray:
    """Normalize features using per-feature normalization."""
    mean = np.mean(features, axis=0, keepdims=True)
    std = np.std(features, axis=0, keepdims=True) + 1e-8
    return (features - mean) / std


def extract_features(audio: np.ndarray) -> np.ndarray:
    """Extract and normalize features from audio."""
    audio = fix_audio_length(audio, AUDIO_SAMPLES)
    features = compute_mfcc(audio)
    features = fix_feature_length(features, EXPECTED_FRAMES)
    features = normalize_features(features)
    return features.astype(np.float32)


def fix_feature_length(features: np.ndarray, target_frames: int) -> np.ndarray:
    """Pad or trim features to target number of frames."""
    if features.shape[0] > target_frames:
        return features[:target_frames]
    elif features.shape[0] < target_frames:
        pad_width = ((0, target_frames - features.shape[0]), (0, 0))
        return np.pad(features, pad_width, mode='constant')
    return features


def run_keras_inference(model_path: Path, features: np.ndarray) -> np.ndarray:
    """Run inference using Keras model."""
    model = tf.keras.models.load_model(model_path)
    features_batch = features[np.newaxis, ..., np.newaxis]
    predictions = model.predict(features_batch, verbose=0)
    return predictions[0]


def run_tflite_inference(tflite_path: Path, features: np.ndarray) -> np.ndarray:
    """Run inference using TFLite model."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_data = features[np.newaxis, ..., np.newaxis].copy()

    if input_details[0]['dtype'] == np.int8:
        scale, zero_point = input_details[0]['quantization']
        if scale > 0:
            input_data = (input_data / scale + zero_point).astype(np.int8)

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])

    if output_details[0]['dtype'] == np.int8:
        scale, zero_point = output_details[0]['quantization']
        if scale > 0:
            output = (output.astype(np.float32) - zero_point) * scale

    return output[0]


WAKE_CLASSES = ("zylose", "hey_zylose")
CONFIDENCE_THRESHOLD = 0.70
MARGIN_THRESHOLD = 0.30


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
        return False, pred_class, confidence, f"margin {margin:.2f} < {MARGIN_THRESHOLD:.2f}"

    return True, pred_class, confidence, "passed"


def print_predictions(probs: np.ndarray, label: str = ""):
    """Print class probabilities with rejection logic."""
    print(f"\n{label} Predictions:")
    print("-" * 30)
    for i, cls in enumerate(CLASS_LABELS):
        marker = " *" if cls in WAKE_CLASSES else "  "
        print(f"  {cls:<10}: {probs[i]:.4f}{marker}")

    detected, pred_class, confidence, reason = check_wake_word(probs)
    sorted_probs = np.sort(probs)[::-1]
    margin = sorted_probs[0] - sorted_probs[1]

    print(f"\n  Predicted: {pred_class} (confidence: {confidence:.4f}, margin: {margin:.2f})")
    if detected:
        print(f"  >>> WAKE WORD DETECTED <<<")
    else:
        print(f"  Rejected: {reason}")


def main():
    parser = argparse.ArgumentParser(description="Test inference on audio file")
    parser.add_argument('--file', type=str, required=True, help='Path to WAV file')
    parser.add_argument('--keras-model', type=str, default='zylose_kws.keras', help='Keras model filename')
    parser.add_argument('--tflite-model', type=str, default='zylose_int8.tflite', help='TFLite model filename')
    args = parser.parse_args()

    audio_path = Path(args.file)
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        return

    keras_path = MODELS_DIR / args.keras_model
    tflite_path = MODELS_DIR / args.tflite_model

    print(f"Loading audio: {audio_path}")
    audio = load_audio(audio_path)
    print(f"  Duration: {len(audio)/SAMPLE_RATE:.2f}s, Sample rate: {SAMPLE_RATE} Hz")

    print("Extracting features...")
    features = extract_features(audio)
    print(f"  Feature shape: {features.shape}")

    print("\n" + "="*50)
    print("KERAS INFERENCE")
    print("="*50)
    if keras_path.exists():
        keras_probs = run_keras_inference(keras_path, features)
        print_predictions(keras_probs, "Keras")
    else:
        print(f"Keras model not found: {keras_path}")

    print("\n" + "="*50)
    print("TFLITE INFERENCE")
    print("="*50)
    if tflite_path.exists():
        tflite_probs = run_tflite_inference(tflite_path, features)
        print_predictions(tflite_probs, "TFLite")
    else:
        print(f"TFLite model not found: {tflite_path}")

    if keras_path.exists() and tflite_path.exists():
        diff = np.abs(keras_probs - tflite_probs).max()
        print(f"\nMax difference between Keras and TFLite: {diff:.6f}")


if __name__ == "__main__":
    main()