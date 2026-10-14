#!/usr/bin/env python3
"""
Evaluation script for the trained KWS model.
Computes accuracy, precision, recall, F1, confusion matrix, and per-class metrics.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    DATASET_PROCESSED, MODELS_DIR, RESULTS_DIR, CLASS_LABELS,
    NUM_CLASSES, EXPECTED_FRAMES, NUM_MFCC
)


def load_data_and_model(model_path: Path):
    """Load test data and model."""
    X_test = np.load(DATASET_PROCESSED / "X_test.npy")
    y_test = np.load(DATASET_PROCESSED / "y_test.npy")
    X_test = X_test[..., np.newaxis]

    model = tf.keras.models.load_model(model_path)
    return X_test, y_test, model


def evaluate_model(model, X_test, y_test):
    """Run evaluation and compute all metrics."""
    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average=None, zero_division=0)
    recall = recall_score(y_test, y_pred, average=None, zero_division=0)
    f1 = f1_score(y_test, y_pred, average=None, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    macro_precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
    macro_recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)

    return {
        'accuracy': float(accuracy),
        'precision_per_class': precision.tolist(),
        'recall_per_class': recall.tolist(),
        'f1_per_class': f1.tolist(),
        'macro_precision': float(macro_precision),
        'macro_recall': float(macro_recall),
        'macro_f1': float(macro_f1),
        'confusion_matrix': cm.tolist(),
        'y_pred': y_pred.tolist(),
        'y_pred_proba': y_pred_proba.tolist()
    }


def print_metrics(metrics: dict):
    """Print formatted metrics."""
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Overall Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Macro Precision:   {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:      {metrics['macro_recall']:.4f}")
    print(f"Macro F1:          {metrics['macro_f1']:.4f}")

    print("\nPer-class metrics:")
    print(f"{'Class':<12} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-"*42)
    for i, cls in enumerate(CLASS_LABELS):
        p = metrics['precision_per_class'][i]
        r = metrics['recall_per_class'][i]
        f = metrics['f1_per_class'][i]
        print(f"{cls:<12} {p:>10.4f} {r:>10.4f} {f:>10.4f}")

    zylose_idx = CLASS_LABELS.index('zylose')
    print(f"\n>>> Zylose (wake word) metrics:")
    print(f"    Precision: {metrics['precision_per_class'][zylose_idx]:.4f}")
    print(f"    Recall:    {metrics['recall_per_class'][zylose_idx]:.4f}")
    print(f"    F1 Score:  {metrics['f1_per_class'][zylose_idx]:.4f}")

    print("\nConfusion Matrix:")
    cm = np.array(metrics['confusion_matrix'])
    print(f"           Predicted")
    print(f"        ", end="")
    for cls in CLASS_LABELS:
        print(f"{cls:>10}", end="")
    print()
    for i, cls in enumerate(CLASS_LABELS):
        print(f"Actual {cls:<6}", end="")
        for j in range(NUM_CLASSES):
            print(f"{cm[i,j]:>10}", end="")
        print()

    print("\nClassification Report:")
    y_test = np.load(DATASET_PROCESSED / "y_test.npy")
    y_pred = np.array(metrics['y_pred'])
    print(classification_report(y_test, y_pred, target_names=CLASS_LABELS, zero_division=0))


def plot_confusion_matrix(metrics: dict, save_path: Path):
    """Plot and save confusion matrix."""
    cm = np.array(metrics['confusion_matrix'])
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=CLASS_LABELS, yticklabels=CLASS_LABELS, ax=axes[0])
    axes[0].set_xlabel('Predicted')
    axes[0].set_ylabel('Actual')
    axes[0].set_title('Confusion Matrix (Counts)')

    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=CLASS_LABELS, yticklabels=CLASS_LABELS, ax=axes[1])
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('Actual')
    axes[1].set_title('Confusion Matrix (Normalized)')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_training_history(log_dir: Path, save_path: Path):
    """Plot training history from log."""
    history_path = log_dir / "history.json"
    if not history_path.exists():
        return

    with open(history_path, 'r') as f:
        history = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history['loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history['accuracy'], label='Train Acc')
    axes[1].plot(history['val_accuracy'], label='Val Acc')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained KWS model")
    parser.add_argument('--model', type=str, default='zylose_kws.keras', help='Model filename')
    args = parser.parse_args()

    model_path = MODELS_DIR / args.model
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        return

    print(f"Loading model from: {model_path}")
    X_test, y_test, model = load_data_and_model(model_path)

    print("Running evaluation...")
    metrics = evaluate_model(model, X_test, y_test)
    print_metrics(metrics)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_path = RESULTS_DIR / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to: {metrics_path}")

    cm_path = RESULTS_DIR / "confusion_matrix.png"
    plot_confusion_matrix(metrics, cm_path)
    print(f"Confusion matrix saved to: {cm_path}")

    log_dir = MODELS_DIR.parent / "logs" / "training"
    history_plot_path = RESULTS_DIR / "training_history.png"
    plot_training_history(log_dir, history_plot_path)
    print(f"Training history plot saved to: {history_plot_path}")

    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()