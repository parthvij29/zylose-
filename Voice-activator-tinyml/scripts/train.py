#!/usr/bin/env python3
"""
Training script for the TinyML KWS model.
Loads features, trains model with callbacks, saves best model and history.
"""

import argparse
import json
import os
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import (
    EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, CSVLogger
)
import matplotlib.pyplot as plt

from config import (
    DATASET_PROCESSED, MODELS_DIR, LOGS_DIR, CLASS_LABELS,
    NUM_CLASSES, EXPECTED_FRAMES, NUM_MFCC, RANDOM_SEED
)
from model import create_model, print_model_info


def load_data():
    """Load precomputed features."""
    X_train = np.load(DATASET_PROCESSED / "X_train.npy")
    y_train = np.load(DATASET_PROCESSED / "y_train.npy")
    X_val = np.load(DATASET_PROCESSED / "X_val.npy")
    y_val = np.load(DATASET_PROCESSED / "y_val.npy")
    X_test = np.load(DATASET_PROCESSED / "X_test.npy")
    y_test = np.load(DATASET_PROCESSED / "y_test.npy")

    X_train = X_train[..., np.newaxis]
    X_val = X_val[..., np.newaxis]
    X_test = X_test[..., np.newaxis]

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


def get_callbacks(model_path: Path, log_dir: Path):
    """Get training callbacks."""
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1,
            min_delta=1e-4
        ),
        ModelCheckpoint(
            filepath=str(model_path),
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=7,
            min_lr=1e-6,
            verbose=1
        ),
        CSVLogger(str(log_dir / "training_log.csv"))
    ]
    return callbacks


def plot_history(history, save_path: Path):
    """Plot training history."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history.history['loss'], label='Train Loss')
    axes[0].plot(history.history['val_loss'], label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history.history['accuracy'], label='Train Acc')
    axes[1].plot(history.history['val_accuracy'], label='Val Acc')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Train TinyML KWS model")
    parser.add_argument('--epochs', type=int, default=100, help='Maximum epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3, help='Initial learning rate')
    parser.add_argument('--model-name', type=str, default='zylose_kws.keras', help='Model filename')
    args = parser.parse_args()

    tf.keras.utils.set_random_seed(RANDOM_SEED)

    print("Loading data...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_data()

    print(f"Train: {X_train.shape}, {y_train.shape}")
    print(f"Val:   {X_val.shape}, {y_val.shape}")
    print(f"Test:  {X_test.shape}, {y_test.shape}")

    input_shape = X_train.shape[1:]
    model = create_model(input_shape, NUM_CLASSES)
    print_model_info(model, input_shape)

    optimizer = tf.keras.optimizers.Adam(learning_rate=args.lr)
    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    model_path = MODELS_DIR / args.model_name
    log_dir = LOGS_DIR / "training"
    log_dir.mkdir(parents=True, exist_ok=True)

    callbacks = get_callbacks(model_path, log_dir)

    print(f"\nStarting training for {args.epochs} epochs...")
    print(f"Batch size: {args.batch_size}")
    print(f"Initial LR: {args.lr}")
    print(f"Model will be saved to: {model_path}")

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1
    )

    print("\nTraining complete!")
    print(f"Best model saved to: {model_path}")

    history_path = log_dir / "history.json"
    with open(history_path, 'w') as f:
        json.dump({k: [float(v) for v in vals] for k, vals in history.history.items()}, f, indent=2)

    plot_path = log_dir / "training_history.png"
    plot_history(history, plot_path)
    print(f"Training history plot saved to: {plot_path}")

    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest Loss: {test_loss:.4f}")
    print(f"Test Accuracy: {test_acc:.4f}")

    with open(log_dir / "test_results.json", 'w') as f:
        json.dump({"test_loss": float(test_loss), "test_accuracy": float(test_acc)}, f, indent=2)

    from config import save_class_labels
    save_class_labels()
    print(f"Class labels saved to: {MODELS_DIR / 'class_labels.json'}")


if __name__ == "__main__":
    main()