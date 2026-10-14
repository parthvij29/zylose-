# Low Latency and Efficient Voice Activator for Edge Devices

**Smart India Hackathon (SIH) Project for ISRO**

## Project Overview

This project implements a complete TinyML Keyword Spotting (KWS) training pipeline for a custom wake word **"Zylose"** (pronounced **ZAI-LOSE**). The target deployment platform is an **ESP32-S3** with an **INMP441 I2S microphone**.

### Key Constraints (SIH/ISRO Requirements)

- **Target Device**: ESP32-S3 (Xtensa LX7 dual-core @ 240 MHz, 512 KB SRAM)
- **RAM Budget**: < 256 KB for KWS application/runtime
- **CPU Budget**: < 10% utilization during idle continuous listening
- **Model Size Target**: < 100 KB (INT8 quantized)
- **Frameworks**: Open-source only (TensorFlow/Keras, NumPy, Librosa)
- **No Proprietary SDKs**: No Alexa, Google Assistant, Edge Impulse, or commercial wake-word engines
- **Custom Keyword**: Must train specifically for "Zylose" from scratch

## Hardware Target

| Component | Specification |
|-----------|---------------|
| MCU | ESP32-S3 (Xtensa LX7, 240 MHz, 512 KB SRAM, 384 KB ROM) |
| Microphone | INMP441 I2S MEMS microphone (bottom port, 26 dBFS sensitivity) |
| Audio Format | 16 kHz, mono, 16-bit PCM |
| Wake Word | "Zylose" (ZAI-LOSE) |

## Software Requirements

- Python 3.11+
- TensorFlow 2.15+
- NumPy, Librosa, SoundFile, scikit-learn, Matplotlib, Pandas

## Installation

```bash
# Clone and enter project
cd voice-activator-tinyml

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
voice_activator/
├── README.md
├── requirements.txt
├── .gitignore
│
├── dataset/
│   ├── raw/
│   │   ├── zylose/       # "Zylose" recordings
│   │   ├── unknown/      # Random speech, conversations, similar words
│   │   └── silence/      # Ambient noise, room tone, fan, keyboard
│   │
│   ├── processed/        # Resampled, split (train/val/test)
│   └── augmented/        # Augmented training samples
│
├── scripts/
│   ├── record_audio.py       # Record dataset samples
│   ├── preprocess.py         # Validate, resample, split dataset
│   ├── augment_audio.py      # Augment training data
│   ├── extract_features.py   # Compute MFCC features
│   ├── train.py              # Train the model
│   ├── evaluate.py           # Evaluate on test set
│   ├── convert_tflite.py     # Convert to FP32/INT8 TFLite
│   ├── test_inference.py     # Test single WAV file
│   └── false_activation_test.py  # Continuous listening simulation
│
├── models/                 # Saved models and configs
├── logs/                   # Training logs
├── results/                # Evaluation results, plots
└── notebooks/              # Jupyter notebooks
```

## Dataset Collection

### Three Classes Required

| Class | Label | Description | Target Samples |
|-------|-------|-------------|----------------|
| Silence | 0 | Room ambience, fan, keyboard, environmental noise | 500+ |
| Unknown | 1 | Random words, phrases, conversations, similar-sounding words | 1000+ |
| Zylose | 2 | People saying "Zylose" (ZAI-LOSE) | 500+ |

### Recording Samples

```bash
# Record wake word samples
python scripts/record_audio.py --class zylose --speaker speaker01 --count 50

# Record unknown speech
python scripts/record_audio.py --class unknown --speaker speaker01 --count 100

# Record silence/ambient
python scripts/record_audio.py --class silence --speaker room01 --count 50
```

**Recording workflow:**
1. Select class (zylose/unknown/silence)
2. Enter speaker ID (e.g., `speaker01`, `room01`)
3. Enter number of recordings
4. Script shows 3-2-1 countdown
5. Records ~1-2 seconds
6. Saves as: `zylose_speaker01_0001.wav` (16 kHz, mono, 16-bit WAV)

**Tips for quality data:**
- **Zylose**: Vary pronunciation, speed, emphasis; multiple speakers; different distances
- **Unknown**: Include "Zylose"-sounding words (xylose, zylose variants), conversations, random words
- **Silence**: Record in target environment; include fan, AC, typing, traffic noise

## Preprocessing

```bash
python scripts/preprocess.py
```

**What it does:**
- Validates dataset structure and reports sample counts
- Resamples all audio to 16 kHz mono
- Fixes length to exactly 1 second (16000 samples)
- Normalizes amplitude
- Creates **speaker-aware splits** (70% train / 15% val / 15% test)
- Saves split info to `dataset/processed/split_info.json`

## Data Augmentation (Training Only)

```bash
python scripts/augment_audio.py --factor 3
```

**Augmentations applied:**
- Random gain (±6 dB)
- Time shift (±100 ms)
- Additive Gaussian noise (0-5%)
- Mild reverberation (10% probability)
- Random silence offset (0-200 ms)

Generates 3x augmented samples in `dataset/augmented/`

## Feature Extraction

```bash
python scripts/extract_features.py --feature-type mfcc --use-augmented
```

**Configuration:**
- Sample rate: 16000 Hz
- Window: 30 ms (480 samples)
- Hop: 10 ms (160 samples)
- Mel bins: 40
- MFCC coefficients: 13
- Expected frames: ~98
- Normalization: Per-feature (mean=0, std=1)

Saves:
- `dataset/processed/X_train.npy`, `y_train.npy` (and val/test)
- `models/feature_config.json` (for ESP32 deployment)

## Training

```bash
python scripts/train.py --epochs 100 --batch-size 32 --lr 1e-3
```

**Model Architecture (TinyML CNN):**
```
Input: (98, 13, 1)
↓ Conv2D(16, 3×3) + BN + ReLU
↓ DepthwiseConv2D(3×3) + BN + ReLU
↓ DepthwiseConv2D(3×3, stride=2) + BN + ReLU
↓ GlobalAveragePooling2D
↓ Dense(16) + ReLU + Dropout(0.1)
↓ Dense(3) + Softmax
```

**Training Features:**
- Early stopping (patience=15)
- Model checkpointing (best val_loss)
- LR reduction on plateau (factor=0.5, patience=7)
- L2 regularization (1e-4)
- Fixed random seed (42) for reproducibility

**Expected Output:**
- ~15-25K parameters
- ~60-100 KB FP32 / ~15-25 KB INT8
- Training history saved to `logs/training/`

## Evaluation

```bash
python scripts/evaluate.py
```

**Metrics computed:**
- Overall accuracy, macro precision/recall/F1
- **Per-class metrics** (critical for zylose class)
- Confusion matrix (counts + normalized)
- Classification report

**Key Metrics to Watch:**
- **Zylose Precision**: Of all "Zylose" predictions, how many are correct?
- **Zylose Recall**: Of all actual "Zylose", how many detected?
- **Zylose F1**: Harmonic mean of precision/recall

Saves:
- `results/metrics.json`
- `results/confusion_matrix.png`
- `results/training_history.png`

## TFLite Conversion

```bash
python scripts/convert_tflite.py
```

**Outputs:**
- `models/zylose_fp32.tflite` - Float32 model
- `models/zylose_int8.tflite` - Fully INT8 quantized

**Quantization:**
- Post-training quantization with representative dataset (100 samples)
- INT8 input/output where possible
- Optimized for TFLite Micro operators

**Validation:**
- Compares Keras vs FP32 vs INT8 accuracy on test set
- Reports operator compatibility for TFLite Micro

## Test Inference

```bash
python scripts/test_inference.py --file path/to/audio.wav
```

**Output:**
```
silence: 0.01
unknown: 0.03
zylose: 0.96

WAKE WORD DETECTED
```

Runs both Keras and INT8 TFLite inference for comparison.

## False Activation Testing

```bash
python scripts/false_activation_test.py --model zylose_int8.tflite
```

**Simulates continuous listening:**
- 1-second windows with 100ms hop
- Requires 2 consecutive detections > 0.85 threshold
- 2-second cooldown after trigger

**Reports:**
- False positives per hour (on unknown/silence)
- Wake word detection rate (on zylose samples)
- Individual detection timestamps

## ESP32 Deployment Preparation

The pipeline generates all artifacts needed for ESP32-S3 deployment:

### `models/feature_config.json`
```json
{
  "sample_rate": 16000,
  "audio_duration": 1.0,
  "window_length_ms": 30,
  "frame_step_ms": 10,
  "num_mel_bins": 40,
  "num_mfcc": 13,
  "n_fft": 480,
  "hop_length": 160,
  "expected_frames": 98,
  "normalization": "per_feature"
}
```

### `models/class_labels.json`
```json
["silence", "unknown", "zylose"]
```

### `models/zylose_int8.tflite` - Ready for TFLite Micro

## ESP32-S3 Deployment Roadmap

### 1. Audio Capture (INMP441 I2S)
```c
// I2S configuration for INMP441
i2s_config_t i2s_config = {
    .mode = I2S_MODE_MASTER | I2S_MODE_RX,
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
};
```

### 2. Feature Extraction on ESP32
- Implement MFCC using fixed-point arithmetic
- Use `dsps_fft2r_fc32` from ESP-DSP library
- Pre-compute Mel filterbank and DCT matrix
- Match Python normalization exactly (save mean/std per feature)

### 3. Model Conversion to C Array
```bash
xxd -i models/zylose_int8.tflite > models/zylose_model.cc
```

### 4. TFLite Micro Integration
```cpp
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"

// Register required ops
tflite::MicroMutableOpResolver<10> resolver;
resolver.AddDepthwiseConv2D();
resolver.AddConv2D();
resolver.AddAveragePool2D();
resolver.AddFullyConnected();
resolver.AddSoftmax();
resolver.AddReshape();
resolver.AddQuantize();
resolver.AddDequantize();

// Tensor arena (target < 50 KB)
constexpr int kTensorArenaSize = 40 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

// Interpreter
tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, kTensorArenaSize);
```

### 5. Continuous Listening Loop
```cpp
while (true) {
    // 1. Read 1600 samples (100ms) from I2S DMA
    // 2. Accumulate into 16000-sample ring buffer
    // 3. Every 100ms: extract MFCC from latest 16000 samples
    // 4. Run TFLite inference
    // 5. Apply detection logic (threshold + consecutive + cooldown)
    // 6. If triggered: start streaming to ASR server
}
```

## Memory Optimization Strategy

| Component | Est. RAM | Notes |
|-----------|----------|-------|
| TFLite Model (INT8) | ~20 KB | Stored in Flash |
| Tensor Arena | ~40 KB | Configurable |
| Audio Buffer (1s) | 32 KB | int16_t[16000] |
| MFCC Buffer | ~5 KB | float[98×13] or int8[98×13] |
| Feature Mean/Std | ~0.5 KB | float[13]×2 |
| **Total Runtime RAM** | **~100 KB** | Well under 256 KB |

## Expected Performance Targets

| Metric | Target |
|--------|--------|
| Model Size (INT8) | < 100 KB |
| RAM Usage (KWS) | < 256 KB |
| CPU Idle | < 10% |
| Zylose Recall | > 90% |
| Zylose Precision | > 85% |
| False Positives/Hour | < 1 |

## Commands Summary

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Data collection
python scripts/record_audio.py --class zylose --speaker speaker01 --count 50
python scripts/record_audio.py --class unknown --speaker speaker01 --count 100
python scripts/record_audio.py --class silence --speaker room01 --count 50

# Pipeline
python scripts/preprocess.py
python scripts/augment_audio.py --factor 3
python scripts/extract_features.py --feature-type mfcc --use-augmented
python scripts/train.py --epochs 100 --batch-size 32 --lr 1e-3
python scripts/evaluate.py
python scripts/convert_tflite.py
python scripts/test_inference.py --file test.wav
python scripts/false_activation_test.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No audio devices found | Check `python -m sounddevice` |
| Low accuracy | Collect more diverse data; check class balance |
| Model too large | Reduce filters; use more depthwise conv |
| INT8 accuracy drop | Increase representative dataset; check quantization |
| High false positives | Add more unknown/silence data; adjust threshold |

## License

MIT License - Open source for SIH/ISRO competition use.

## Acknowledgments

- TensorFlow/Keras team for TFLite Micro
- ESP-IDF and ESP-DSP libraries
- Smart India Hackathon organizers
- ISRO for the problem statement