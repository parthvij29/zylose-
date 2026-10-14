import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATASET_RAW = PROJECT_ROOT / "dataset" / "raw"
DATASET_PROCESSED = PROJECT_ROOT / "dataset" / "processed"
DATASET_AUGMENTED = PROJECT_ROOT / "dataset" / "augmented"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
RESULTS_DIR = PROJECT_ROOT / "results"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

for d in [DATASET_RAW, DATASET_PROCESSED, DATASET_AUGMENTED, MODELS_DIR, LOGS_DIR, RESULTS_DIR, NOTEBOOKS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

CLASS_LABELS = ["silence", "unknown", "zylose"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_LABELS)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASS_LABELS)}
NUM_CLASSES = len(CLASS_LABELS)

SAMPLE_RATE = 16000
AUDIO_DURATION = 1.0
AUDIO_SAMPLES = int(SAMPLE_RATE * AUDIO_DURATION)

WINDOW_LENGTH_MS = 30
FRAME_STEP_MS = 10
NUM_MEL_BINS = 40
NUM_MFCC = 13

N_FFT = int(SAMPLE_RATE * WINDOW_LENGTH_MS / 1000)
HOP_LENGTH = int(SAMPLE_RATE * FRAME_STEP_MS / 1000)

EXPECTED_FRAMES = int((AUDIO_SAMPLES - N_FFT) / HOP_LENGTH) + 1

RANDOM_SEED = 42
TRAIN_SPLIT = 0.70
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15

AUGMENTATION_CONFIG = {
    "gain_range_db": (-6, 6),
    "time_shift_max_ms": 100,
    "noise_factor_range": (0.0, 0.05),
    "reverb_probability": 0.1,
    "silence_offset_max_ms": 200,
}

DETECTION_CONFIG = {
    "threshold": 0.85,
    "consecutive_detections": 2,
    "cooldown_seconds": 2.0,
    "window_hop_ms": 100,
}

@dataclass
class FeatureConfig:
    sample_rate: int = SAMPLE_RATE
    audio_duration: float = AUDIO_DURATION
    window_length_ms: int = WINDOW_LENGTH_MS
    frame_step_ms: int = FRAME_STEP_MS
    num_mel_bins: int = NUM_MEL_BINS
    num_mfcc: int = NUM_MFCC
    n_fft: int = N_FFT
    hop_length: int = HOP_LENGTH
    expected_frames: int = EXPECTED_FRAMES
    normalization: str = "per_feature"

    def to_dict(self):
        return asdict(self)

    def save(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path):
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

FEATURE_CONFIG = FeatureConfig()

def set_random_seeds(seed: int = RANDOM_SEED):
    import random
    import numpy as np
    import tensorflow as tf
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_feature_config_path() -> Path:
    return MODELS_DIR / "feature_config.json"

def get_class_labels_path() -> Path:
    return MODELS_DIR / "class_labels.json"

def save_class_labels(path: Optional[Path] = None):
    path = path or get_class_labels_path()
    with open(path, 'w') as f:
        json.dump(CLASS_LABELS, f, indent=2)

def load_class_labels(path: Optional[Path] = None) -> list:
    path = path or get_class_labels_path()
    with open(path, 'r') as f:
        return json.load(f)