#!/usr/bin/env python3
"""
Preprocessing script: validates dataset structure, converts all audio to 16kHz mono 16-bit WAV,
and creates train/val/test splits with speaker-aware splitting.
"""

import argparse
import json
import random
import shutil
from pathlib import Path
from collections import defaultdict
import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm

from config import (
    DATASET_RAW, DATASET_PROCESSED, CLASS_LABELS, CLASS_TO_IDX,
    SAMPLE_RATE, AUDIO_DURATION, AUDIO_SAMPLES, RANDOM_SEED,
    TRAIN_SPLIT, VAL_SPLIT, TEST_SPLIT
)


def validate_dataset_structure() -> dict:
    """Validate dataset structure and count samples per class."""
    stats = {}
    total = 0
    for cls in CLASS_LABELS:
        class_dir = DATASET_RAW / cls
        if class_dir.exists():
            files = list(class_dir.glob("*.wav"))
            stats[cls] = len(files)
            total += len(files)
        else:
            stats[cls] = 0
            print(f"Warning: {class_dir} does not exist")
    stats['total'] = total
    return stats


def parse_speaker_id(filename: str) -> str:
    """Extract speaker ID from filename (format: class_speakerID_number.wav)."""
    parts = filename.split('_')
    if len(parts) >= 2:
        return parts[1]
    return "unknown"


def load_and_resample_audio(filepath: Path, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load audio and resample to target sample rate."""
    audio, sr = sf.read(str(filepath))
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    if sr != target_sr:
        audio = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=target_sr)
    return audio


def fix_audio_length(audio: np.ndarray, target_samples: int = AUDIO_SAMPLES) -> np.ndarray:
    """Pad or trim audio to target length."""
    if len(audio) > target_samples:
        return audio[:target_samples]
    elif len(audio) < target_samples:
        pad = np.zeros(target_samples - len(audio), dtype=audio.dtype)
        return np.concatenate([audio, pad])
    return audio


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """Normalize audio to [-1, 1] range."""
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95
    return audio


def process_audio_file(src: Path, dst: Path):
    """Process a single audio file: load, resample, fix length, normalize, save as 16-bit WAV."""
    audio = load_and_resample_audio(src)
    audio = fix_audio_length(audio)
    audio = normalize_audio(audio)
    audio_int16 = (audio * 32767).astype(np.int16)
    sf.write(str(dst), audio_int16, SAMPLE_RATE, subtype='PCM_16')


def speaker_aware_split(file_list: list, train_ratio: float, val_ratio: float, test_ratio: float, seed: int = RANDOM_SEED):
    """Split files by speaker to avoid data leakage.
    When a speaker has enough files, also splits within that speaker."""
    random.seed(seed)
    np.random.seed(seed)

    speaker_files = defaultdict(list)
    for f in file_list:
        speaker = parse_speaker_id(f.name)
        speaker_files[speaker].append(f)

    speakers = list(speaker_files.keys())
    random.shuffle(speakers)

    train_files = []
    val_files = []
    test_files = []
    train_speakers = []
    val_speakers = []
    test_speakers = []

    for speaker in speakers:
        files = speaker_files[speaker]
        random.shuffle(files)

        n = len(files)
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio))
        n_test = n - n_train - n_val

        if n_test < 0:
            n_val = max(0, n - n_train)
            n_test = 0

        train_files.extend(files[:n_train])
        val_files.extend(files[n_train:n_train + n_val])
        test_files.extend(files[n_train + n_val:])

        if n_train > 0:
            train_speakers.append(speaker)
        if n_val > 0:
            val_speakers.append(speaker)
        if n_test > 0:
            test_speakers.append(speaker)

    return train_files, val_files, test_files, {
        'train_speakers': train_speakers,
        'val_speakers': val_speakers,
        'test_speakers': test_speakers
    }


def create_splits():
    """Create train/val/test splits and copy processed files."""
    print("Validating dataset structure...")
    stats = validate_dataset_structure()
    print("\nDataset statistics:")
    for cls, count in stats.items():
        if cls != 'total':
            print(f"  {cls}: {count} samples")
    print(f"  Total: {stats['total']} samples")

    if stats['total'] == 0:
        print("Error: No audio files found. Please record samples first.")
        return

    for split in ['train', 'val', 'test']:
        for cls in CLASS_LABELS:
            (DATASET_PROCESSED / split / cls).mkdir(parents=True, exist_ok=True)

    split_info = {'splits': {}, 'speaker_info': {}}

    for cls in CLASS_LABELS:
        class_dir = DATASET_RAW / cls
        if not class_dir.exists():
            continue

        files = list(class_dir.glob("*.wav"))
        if not files:
            continue

        train_files, val_files, test_files, speaker_info = speaker_aware_split(
            files, TRAIN_SPLIT, VAL_SPLIT, TEST_SPLIT
        )

        split_info['speaker_info'][cls] = speaker_info

        for split_name, file_list in [('train', train_files), ('val', val_files), ('test', test_files)]:
            split_info['splits'][f"{cls}_{split_name}"] = len(file_list)
            for f in tqdm(file_list, desc=f"Processing {cls}/{split_name}"):
                dst = DATASET_PROCESSED / split_name / cls / f.name
                process_audio_file(f, dst)

    split_info_path = DATASET_PROCESSED / "split_info.json"
    with open(split_info_path, 'w') as f:
        json.dump(split_info, f, indent=2)

    print("\nSplit summary:")
    for key, count in split_info['splits'].items():
        print(f"  {key}: {count}")

    print(f"\nSplit info saved to: {split_info_path}")
    print("Preprocessing complete!")


def main():
    parser = argparse.ArgumentParser(description="Preprocess dataset: validate, resample, split")
    parser.add_argument('--force', action='store_true', help='Overwrite existing processed data')
    args = parser.parse_args()

    if DATASET_PROCESSED.exists() and not args.force:
        print(f"Processed dataset already exists at {DATASET_PROCESSED}")
        print("Use --force to overwrite")
        return

    if DATASET_PROCESSED.exists():
        shutil.rmtree(DATASET_PROCESSED)

    create_splits()


if __name__ == "__main__":
    main()