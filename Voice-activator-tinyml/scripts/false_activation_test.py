#!/usr/bin/env python3
"""
False activation testing script.
Simulates continuous listening with overlapping windows to measure false positive rate.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
import soundfile as sf
import librosa
from tqdm import tqdm

from config import (
    DATASET_PROCESSED, DATASET_RAW, MODELS_DIR, RESULTS_DIR,
    SAMPLE_RATE, AUDIO_SAMPLES, FEATURE_CONFIG,
    EXPECTED_FRAMES, NUM_MFCC, CLASS_LABELS,
    N_FFT, HOP_LENGTH, DETECTION_CONFIG
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
    if len(audio) > target_samples:
        return audio[:target_samples]
    elif len(audio) < target_samples:
        return np.pad(audio, (0, target_samples - len(audio)), mode='constant')
    return audio


def compute_mfcc(audio: np.ndarray) -> np.ndarray:
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
    mean = np.mean(features, axis=0, keepdims=True)
    std = np.std(features, axis=0, keepdims=True) + 1e-8
    return (features - mean) / std


def fix_feature_length(features: np.ndarray, target_frames: int) -> np.ndarray:
    if features.shape[0] > target_frames:
        return features[:target_frames]
    elif features.shape[0] < target_frames:
        return np.pad(features, ((0, target_frames - features.shape[0]), (0, 0)), mode='constant')
    return features


def extract_features(audio: np.ndarray) -> np.ndarray:
    audio = fix_audio_length(audio, AUDIO_SAMPLES)
    features = compute_mfcc(audio)
    features = fix_feature_length(features, EXPECTED_FRAMES)
    features = normalize_features(features)
    return features.astype(np.float32)


def load_model(tflite_path: Path):
    """Load TFLite model."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    return interpreter


def run_inference(interpreter, features: np.ndarray) -> np.ndarray:
    """Run single inference."""
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


def simulate_continuous_listening(
    audio: np.ndarray,
    interpreter,
    window_hop_ms: int = 100,
    threshold: float = 0.85,
    consecutive_required: int = 2,
    cooldown_seconds: float = 2.0
):
    """Simulate continuous listening with sliding window."""
    window_samples = AUDIO_SAMPLES
    hop_samples = int(window_hop_ms * SAMPLE_RATE / 1000)
    cooldown_samples = int(cooldown_seconds * SAMPLE_RATE)

    zylose_idx = CLASS_LABELS.index('zylose')

    detections = []
    consecutive_count = 0
    last_trigger_sample = -cooldown_samples

    num_windows = (len(audio) - window_samples) // hop_samples + 1

    for i in range(num_windows):
        start = i * hop_samples
        end = start + window_samples
        window = audio[start:end]

        if len(window) < window_samples:
            window = fix_audio_length(window, window_samples)

        features = extract_features(window)
        probs = run_inference(interpreter, features)
        zylose_prob = probs[zylose_idx]

        if zylose_prob >= threshold:
            consecutive_count += 1
        else:
            consecutive_count = 0

        if consecutive_count >= consecutive_required:
            current_sample = start
            if current_sample - last_trigger_sample >= cooldown_samples:
                detections.append({
                    'window_index': i,
                    'sample_index': current_sample,
                    'time_seconds': current_sample / SAMPLE_RATE,
                    'confidence': float(zylose_prob)
                })
                last_trigger_sample = current_sample
                consecutive_count = 0

    return detections


def test_false_activations(model_path: Path, test_dir: Path, label: str):
    """Test false activations on a directory of non-wake-word audio."""
    if not test_dir.exists():
        print(f"Directory not found: {test_dir}")
        return None

    files = list(test_dir.glob("*.wav"))
    if not files:
        print(f"No WAV files in {test_dir}")
        return None

    interpreter = load_model(model_path)

    all_detections = []
    total_duration = 0

    print(f"\nTesting {label} ({len(files)} files)...")
    for f in tqdm(files, desc=label):
        audio = load_audio(f)
        total_duration += len(audio) / SAMPLE_RATE
        detections = simulate_continuous_listening(
            audio, interpreter,
            window_hop_ms=DETECTION_CONFIG['window_hop_ms'],
            threshold=DETECTION_CONFIG['threshold'],
            consecutive_required=DETECTION_CONFIG['consecutive_detections'],
            cooldown_seconds=DETECTION_CONFIG['cooldown_seconds']
        )
        for d in detections:
            d['file'] = f.name
        all_detections.extend(detections)

    false_positives = len(all_detections)
    fps_per_hour = (false_positives / total_duration * 3600) if total_duration > 0 else 0

    print(f"  Total duration: {total_duration:.1f}s ({total_duration/3600:.2f}h)")
    print(f"  False activations: {false_positives}")
    print(f"  False activations/hour: {fps_per_hour:.2f}")

    return {
        'label': label,
        'num_files': len(files),
        'total_duration_seconds': total_duration,
        'false_positives': false_positives,
        'false_positives_per_hour': fps_per_hour,
        'detections': all_detections
    }


def test_wake_word_detection(model_path: Path, test_dir: Path):
    """Test wake word detection rate on zylose samples."""
    if not test_dir.exists():
        return None

    files = list(test_dir.glob("*.wav"))
    if not files:
        return None

    interpreter = load_model(model_path)
    zylose_idx = CLASS_LABELS.index('zylose')

    detected = 0
    total = len(files)

    print(f"\nTesting wake word detection ({total} files)...")
    for f in tqdm(files, desc="Wake word"):
        audio = load_audio(f)
        features = extract_features(audio)
        probs = run_inference(interpreter, features)
        if probs[zylose_idx] >= DETECTION_CONFIG['threshold']:
            detected += 1

    detection_rate = detected / total if total > 0 else 0
    print(f"  Detected: {detected}/{total} ({detection_rate*100:.1f}%)")

    return {
        'total': total,
        'detected': detected,
        'detection_rate': detection_rate
    }


def main():
    parser = argparse.ArgumentParser(description="False activation and wake word detection test")
    parser.add_argument('--model', type=str, default='zylose_int8.tflite', help='TFLite model')
    parser.add_argument('--threshold', type=float, default=0.85, help='Detection threshold')
    parser.add_argument('--consecutive', type=int, default=2, help='Consecutive detections required')
    parser.add_argument('--cooldown', type=float, default=2.0, help='Cooldown seconds')
    parser.add_argument('--hop', type=int, default=100, help='Window hop in ms')
    args = parser.parse_args()

    model_path = MODELS_DIR / args.model
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return

    DETECTION_CONFIG['threshold'] = args.threshold
    DETECTION_CONFIG['consecutive_detections'] = args.consecutive
    DETECTION_CONFIG['cooldown_seconds'] = args.cooldown
    DETECTION_CONFIG['window_hop_ms'] = args.hop

    print("="*60)
    print("FALSE ACTIVATION TESTING")
    print("="*60)
    print(f"Model: {model_path}")
    print(f"Threshold: {args.threshold}")
    print(f"Consecutive required: {args.consecutive}")
    print(f"Cooldown: {args.cooldown}s")
    print(f"Window hop: {args.hop}ms")

    results = {}

    # Test on unknown class (random speech, conversations)
    unknown_dir = DATASET_RAW / "unknown"
    results['unknown'] = test_false_activations(model_path, unknown_dir, "Unknown speech")

    # Test on silence class (ambient noise)
    silence_dir = DATASET_RAW / "silence"
    results['silence'] = test_false_activations(model_path, silence_dir, "Silence/ambient")

    # Test wake word detection
    zylose_dir = DATASET_RAW / "zylose"
    results['zylose_detection'] = test_wake_word_detection(model_path, zylose_dir)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / "false_activation_test.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for key, val in results.items():
        if val and 'false_positives_per_hour' in val:
            print(f"{key}: {val['false_positives']} false positives ({val['false_positives_per_hour']:.2f}/hour)")
        elif val and 'detection_rate' in val:
            print(f"{key}: {val['detection_rate']*100:.1f}% detection rate")

    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()