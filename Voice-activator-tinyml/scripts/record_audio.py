#!/usr/bin/env python3
"""
Audio recording script for collecting wake word dataset.
Records 16kHz mono 16-bit WAV files for zylose, unknown, and silence classes.
"""

import argparse
import sys
import time
import wave
from pathlib import Path
import numpy as np
import sounddevice as sd
import soundfile as sf

from config import (
    DATASET_RAW, CLASS_LABELS, SAMPLE_RATE, AUDIO_DURATION,
    AUDIO_SAMPLES, RANDOM_SEED
)


def list_audio_devices():
    """List available audio input devices."""
    devices = sd.query_devices()
    print("\nAvailable audio input devices:")
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']} (channels: {device['max_input_channels']}, sample rate: {device['default_samplerate']})")
    return devices


def select_device(devices):
    """Let user select an audio input device."""
    while True:
        try:
            choice = input("\nSelect device number (press Enter for default): ").strip()
            if not choice:
                return None
            idx = int(choice)
            if 0 <= idx < len(devices) and devices[idx]['max_input_channels'] > 0:
                return idx
            print("Invalid device number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def select_class():
    """Let user select the class to record."""
    print("\nAvailable classes:")
    for i, cls in enumerate(CLASS_LABELS):
        print(f"  [{i}] {cls}")
    while True:
        try:
            choice = input("Select class number: ").strip()
            idx = int(choice)
            if 0 <= idx < len(CLASS_LABELS):
                return CLASS_LABELS[idx]
            print("Invalid class number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def get_speaker_id():
    """Get speaker ID from user."""
    while True:
        speaker_id = input("Enter speaker ID (e.g., speaker01): ").strip()
        if speaker_id:
            return speaker_id
        print("Speaker ID cannot be empty.")


def get_num_recordings():
    """Get number of recordings from user."""
    while True:
        try:
            num = int(input("Enter number of recordings: ").strip())
            if num > 0:
                return num
            print("Number must be positive.")
        except ValueError:
            print("Please enter a valid number.")


def countdown(seconds=3):
    """Show countdown before recording."""
    print("\nGet ready...")
    for i in range(seconds, 0, -1):
        print(f"  {i}")
        time.sleep(1)
    print("  RECORDING")


def record_audio(duration: float, sample_rate: int, device: int = None) -> np.ndarray:
    """Record audio from microphone."""
    print(f"Recording for {duration:.1f} seconds at {sample_rate} Hz...")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        device=device
    )
    sd.wait()
    return recording.flatten()


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """Normalize audio to prevent clipping and convert to int16."""
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95
    return (audio * 32767).astype(np.int16)


def save_wav(audio: np.ndarray, sample_rate: int, filepath: Path):
    """Save audio as 16-bit WAV file."""
    sf.write(str(filepath), audio, sample_rate, subtype='PCM_16')


def get_next_filename(class_dir: Path, speaker_id: str, class_name: str) -> Path:
    """Get next available filename with incrementing number."""
    existing = list(class_dir.glob(f"{class_name}_{speaker_id}_*.wav"))
    max_num = 0
    for f in existing:
        try:
            num = int(f.stem.split('_')[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    next_num = max_num + 1
    return class_dir / f"{class_name}_{speaker_id}_{next_num:04d}.wav"


def main():
    parser = argparse.ArgumentParser(description="Record audio samples for wake word dataset")
    parser.add_argument('--class', dest='class_name', choices=CLASS_LABELS, help='Class to record')
    parser.add_argument('--speaker', help='Speaker ID')
    parser.add_argument('--count', type=int, help='Number of recordings')
    parser.add_argument('--duration', type=float, default=AUDIO_DURATION, help='Recording duration in seconds')
    parser.add_argument('--device', type=int, help='Audio device index')
    parser.add_argument('--list-devices', action='store_true', help='List audio devices and exit')
    args = parser.parse_args()

    devices = sd.query_devices()

    if args.list_devices:
        list_audio_devices()
        return

    class_name = args.class_name or select_class()
    speaker_id = args.speaker or get_speaker_id()
    num_recordings = args.count or get_num_recordings()
    duration = args.duration
    device = args.device

    if device is not None:
        if device >= len(devices) or devices[device]['max_input_channels'] == 0:
            print(f"Invalid device {device}")
            list_audio_devices()
            return
    else:
        list_audio_devices()
        device = select_device(devices)

    class_dir = DATASET_RAW / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nRecording {num_recordings} samples for class '{class_name}' as '{speaker_id}'")
    print(f"Saving to: {class_dir}")
    print(f"Duration: {duration}s, Sample rate: {SAMPLE_RATE} Hz, Mono, 16-bit WAV")

    for i in range(num_recordings):
        print(f"\n--- Recording {i+1}/{num_recordings} ---")
        countdown(3)

        audio = record_audio(duration, SAMPLE_RATE, device)
        audio = normalize_audio(audio)

        if len(audio) > SAMPLE_RATE * duration:
            audio = audio[:int(SAMPLE_RATE * duration)]
        elif len(audio) < SAMPLE_RATE * duration:
            pad = np.zeros(int(SAMPLE_RATE * duration) - len(audio), dtype=np.int16)
            audio = np.concatenate([audio, pad])

        filepath = get_next_filename(class_dir, speaker_id, class_name)
        save_wav(audio, SAMPLE_RATE, filepath)
        print(f"Saved: {filepath.name} ({len(audio)/SAMPLE_RATE:.2f}s)")

    print(f"\nDone! Recorded {num_recordings} samples to {class_dir}")


if __name__ == "__main__":
    main()