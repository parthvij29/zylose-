#!/usr/bin/env python3
"""
Data augmentation script for training data only.
Applies: random gain, time shifting, additive noise, mild reverberation, silence offset.
"""

import argparse
import json
import random
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm

from config import (
    DATASET_PROCESSED, DATASET_AUGMENTED, CLASS_LABELS,
    SAMPLE_RATE, AUDIO_SAMPLES, RANDOM_SEED,
    AUGMENTATION_CONFIG
)


def set_seeds(seed: int = RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)


def apply_gain(audio: np.ndarray, gain_db_range: tuple) -> np.ndarray:
    """Apply random gain in dB."""
    gain_db = np.random.uniform(*gain_db_range)
    gain_linear = 10 ** (gain_db / 20.0)
    return audio * gain_linear


def apply_time_shift(audio: np.ndarray, max_shift_ms: int, sample_rate: int) -> np.ndarray:
    """Apply small random time shift."""
    max_shift_samples = int(max_shift_ms * sample_rate / 1000)
    shift = np.random.randint(-max_shift_samples, max_shift_samples + 1)
    if shift > 0:
        return np.pad(audio[:-shift], (shift, 0), mode='constant')
    elif shift < 0:
        return np.pad(audio[-shift:], (0, -shift), mode='constant')
    return audio


def apply_additive_noise(audio: np.ndarray, noise_factor_range: tuple) -> np.ndarray:
    """Add random Gaussian noise."""
    noise_factor = np.random.uniform(*noise_factor_range)
    noise = np.random.randn(len(audio)) * noise_factor
    return audio + noise


def apply_reverb(audio: np.ndarray, sample_rate: int, probability: float = 0.1) -> np.ndarray:
    """Apply mild reverberation using a simple exponential decay."""
    if np.random.random() > probability:
        return audio

    rt60 = np.random.uniform(0.1, 0.3)
    decay = np.exp(-3 * np.log(10) * np.arange(len(audio)) / (rt60 * sample_rate))
    reverb_tail = audio * decay
    reverb_tail = np.roll(reverb_tail, int(0.01 * sample_rate))
    reverb_tail[:int(0.01 * sample_rate)] = 0
    return audio + 0.3 * reverb_tail


def apply_silence_offset(audio: np.ndarray, max_offset_ms: int, sample_rate: int) -> np.ndarray:
    """Add random silence at the beginning."""
    max_offset = int(max_offset_ms * sample_rate / 1000)
    offset = np.random.randint(0, max_offset + 1)
    if offset > 0:
        return np.pad(audio[:-offset], (offset, 0), mode='constant')
    return audio


def augment_audio(audio: np.ndarray, config: dict, sample_rate: int) -> np.ndarray:
    """Apply all augmentations in sequence."""
    audio = apply_gain(audio, config['gain_range_db'])
    audio = apply_time_shift(audio, config['time_shift_max_ms'], sample_rate)
    audio = apply_additive_noise(audio, config['noise_factor_range'])
    audio = apply_reverb(audio, sample_rate, config['reverb_probability'])
    audio = apply_silence_offset(audio, config['silence_offset_max_ms'], sample_rate)

    max_val = np.max(np.abs(audio))
    if max_val > 1.0:
        audio = audio / max_val * 0.95

    return audio


def main():
    parser = argparse.ArgumentParser(description="Augment training audio data")
    parser.add_argument('--factor', type=int, default=3, help='Augmentation factor (how many augmented versions per original)')
    parser.add_argument('--config', type=str, help='Path to augmentation config JSON')
    args = parser.parse_args()

    set_seeds()

    train_dir = DATASET_PROCESSED / "train"
    if not train_dir.exists():
        print(f"Error: Training data not found at {train_dir}")
        print("Run preprocess.py first")
        return

    if DATASET_AUGMENTED.exists():
        import shutil
        shutil.rmtree(DATASET_AUGMENTED)

    for cls in CLASS_LABELS:
        (DATASET_AUGMENTED / cls).mkdir(parents=True, exist_ok=True)

    config = AUGMENTATION_CONFIG.copy()
    if args.config:
        with open(args.config, 'r') as f:
            config.update(json.load(f))

    print(f"Augmentation config: {config}")
    print(f"Augmentation factor: {args.factor}")

    stats = {cls: 0 for cls in CLASS_LABELS}

    for cls in CLASS_LABELS:
        src_dir = train_dir / cls
        if not src_dir.exists():
            continue

        files = list(src_dir.glob("*.wav"))
        print(f"\nAugmenting {cls}: {len(files)} original files")

        for f in tqdm(files, desc=f"Augmenting {cls}"):
            audio, _ = sf.read(str(f))
            audio = audio.astype(np.float32)

            for i in range(args.factor):
                aug_audio = augment_audio(audio.copy(), config, SAMPLE_RATE)
                aug_audio_int16 = (aug_audio * 32767).astype(np.int16)

                stem = f.stem
                aug_name = f"{stem}_aug{i:02d}.wav"
                dst = DATASET_AUGMENTED / cls / aug_name
                sf.write(str(dst), aug_audio_int16, SAMPLE_RATE, subtype='PCM_16')
                stats[cls] += 1

    print("\nAugmentation complete!")
    print("Augmented samples per class:")
    for cls, count in stats.items():
        print(f"  {cls}: {count}")

    with open(DATASET_AUGMENTED / "augmentation_config.json", 'w') as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    main()