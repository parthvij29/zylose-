#!/usr/bin/env python3
"""
Feature extraction: compute MFCC/log-Mel features from audio.
Saves feature extraction config for ESP32 deployment.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm

from config import (
    DATASET_PROCESSED, DATASET_AUGMENTED, CLASS_LABELS, CLASS_TO_IDX,
    SAMPLE_RATE, AUDIO_SAMPLES, FEATURE_CONFIG,
    WINDOW_LENGTH_MS, FRAME_STEP_MS, NUM_MEL_BINS, NUM_MFCC,
    N_FFT, HOP_LENGTH, EXPECTED_FRAMES,
    get_feature_config_path
)


def compute_mfcc(audio: np.ndarray, sr: int, config: FEATURE_CONFIG) -> np.ndarray:
    """Compute MFCC features from audio."""
    mfcc = librosa.feature.mfcc(
        y=audio.astype(np.float32),
        sr=sr,
        n_mfcc=config.num_mfcc,
        n_fft=config.n_fft,
        hop_length=config.hop_length,
        n_mels=config.num_mel_bins,
        fmin=0,
        fmax=sr // 2
    )
    return mfcc.T


def compute_log_mel(audio: np.ndarray, sr: int, config: FEATURE_CONFIG) -> np.ndarray:
    """Compute log-Mel spectrogram features from audio."""
    mel_spec = librosa.feature.melspectrogram(
        y=audio.astype(np.float32),
        sr=sr,
        n_fft=config.n_fft,
        hop_length=config.hop_length,
        n_mels=config.num_mel_bins,
        fmin=0,
        fmax=sr // 2,
        power=2.0
    )
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)
    return log_mel.T


def normalize_features(features: np.ndarray, method: str = "per_feature") -> np.ndarray:
    """Normalize features."""
    if method == "per_feature":
        mean = np.mean(features, axis=0, keepdims=True)
        std = np.std(features, axis=0, keepdims=True) + 1e-8
        return (features - mean) / std
    elif method == "global":
        mean = np.mean(features)
        std = np.std(features) + 1e-8
        return (features - mean) / std
    return features


def fix_feature_length(features: np.ndarray, target_frames: int) -> np.ndarray:
    """Pad or trim features to target number of frames."""
    if features.shape[0] > target_frames:
        return features[:target_frames]
    elif features.shape[0] < target_frames:
        pad_width = ((0, target_frames - features.shape[0]), (0, 0))
        return np.pad(features, pad_width, mode='constant')
    return features


def extract_features_from_file(filepath: Path, feature_type: str = "mfcc") -> np.ndarray:
    """Extract features from a single audio file."""
    audio, sr = sf.read(str(filepath))
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    if sr != SAMPLE_RATE:
        audio = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=SAMPLE_RATE)
    audio = fix_audio_length(audio, AUDIO_SAMPLES)

    if feature_type == "mfcc":
        features = compute_mfcc(audio, SAMPLE_RATE, FEATURE_CONFIG)
    elif feature_type == "logmel":
        features = compute_log_mel(audio, SAMPLE_RATE, FEATURE_CONFIG)
    else:
        raise ValueError(f"Unknown feature type: {feature_type}")

    features = fix_feature_length(features, EXPECTED_FRAMES)
    features = normalize_features(features, FEATURE_CONFIG.normalization)

    return features.astype(np.float32)


def process_split(split: str, feature_type: str = "mfcc", use_augmented: bool = False):
    """Process all files in a split."""
    if use_augmented and split == "train":
        src_root = DATASET_AUGMENTED
    else:
        src_root = DATASET_PROCESSED / split

    if not src_root.exists():
        print(f"Warning: {src_root} does not exist")
        return None, None

    all_features = []
    all_labels = []

    for cls in CLASS_LABELS:
        cls_dir = src_root / cls
        if not cls_dir.exists():
            continue

        files = list(cls_dir.glob("*.wav"))
        for f in tqdm(files, desc=f"Extracting {split}/{cls}"):
            try:
                features = extract_features_from_file(f, feature_type)
                all_features.append(features)
                all_labels.append(CLASS_TO_IDX[cls])
            except Exception as e:
                print(f"Error processing {f}: {e}")

    if not all_features:
        return None, None

    X = np.stack(all_features)
    y = np.array(all_labels, dtype=np.int32)

    return X, y


def fix_audio_length(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Pad or trim audio to target length."""
    if len(audio) > target_samples:
        return audio[:target_samples]
    elif len(audio) < target_samples:
        pad = np.zeros(target_samples - len(audio), dtype=audio.dtype)
        return np.concatenate([audio, pad])
    return audio


def main():
    parser = argparse.ArgumentParser(description="Extract MFCC/log-Mel features from audio")
    parser.add_argument('--feature-type', choices=['mfcc', 'logmel'], default='mfcc', help='Feature type to extract')
    parser.add_argument('--use-augmented', action='store_true', help='Use augmented data for training split')
    args = parser.parse_args()

    feature_type = args.feature_type
    use_augmented = args.use_augmented

    print(f"Feature type: {feature_type}")
    print(f"Use augmented training data: {use_augmented}")
    print(f"Feature config: {FEATURE_CONFIG.to_dict()}")
    print(f"Expected input shape: (1, {EXPECTED_FRAMES}, {FEATURE_CONFIG.num_mfcc if feature_type == 'mfcc' else NUM_MEL_BINS}, 1)")

    for split in ['train', 'val', 'test']:
        print(f"\nProcessing {split} split...")
        X, y = process_split(split, feature_type, use_augmented and split == 'train')
        if X is not None:
            print(f"  {split} features shape: {X.shape}")
            print(f"  {split} labels shape: {y.shape}")
            np.save(DATASET_PROCESSED / f"X_{split}.npy", X)
            np.save(DATASET_PROCESSED / f"y_{split}.npy", y)
        else:
            print(f"  No data for {split}")

    FEATURE_CONFIG.save(get_feature_config_path())
    print(f"\nFeature config saved to: {get_feature_config_path()}")
    print("Feature extraction complete!")


if __name__ == "__main__":
    main()