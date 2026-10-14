#!/usr/bin/env python3
"""
TFLite conversion script: converts Keras model to FP32 and INT8 TFLite.
Uses representative dataset for post-training quantization.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf

from config import (
    DATASET_PROCESSED, MODELS_DIR, EXPECTED_FRAMES, NUM_MFCC,
    RANDOM_SEED
)


def get_representative_dataset(num_samples: int = 100):
    """Generate representative dataset for quantization calibration."""
    X_train = np.load(DATASET_PROCESSED / "X_train.npy")
    X_train = X_train[..., np.newaxis].astype(np.float32)

    indices = np.random.choice(len(X_train), min(num_samples, len(X_train)), replace=False)
    for idx in indices:
        yield [X_train[idx:idx+1]]


def convert_fp32(model, output_path: Path):
    """Convert to FP32 TFLite."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    output_path.write_bytes(tflite_model)
    print(f"FP32 model saved to: {output_path} ({len(tflite_model)/1024:.1f} KB)")
    return tflite_model


def convert_int8(model, output_path: Path):
    """Convert to fully INT8 quantized TFLite."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: get_representative_dataset(100)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()
    output_path.write_bytes(tflite_model)
    print(f"INT8 model saved to: {output_path} ({len(tflite_model)/1024:.1f} KB)")
    return tflite_model


def validate_tflite_model(tflite_path: Path, X_test: np.ndarray, y_test: np.ndarray, input_type: str = 'float32'):
    """Validate TFLite model on test set."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    print(f"\nModel: {tflite_path.name}")
    print(f"Input details: {input_details}")
    print(f"Output details: {output_details}")

    correct = 0
    total = len(X_test)

    for i in range(total):
        input_data = X_test[i:i+1].copy()

        if input_type == 'int8':
            scale, zero_point = input_details[0]['quantization']
            if scale > 0:
                input_data = (input_data / scale + zero_point).astype(np.int8)

        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])

        pred = np.argmax(output)
        if pred == y_test[i]:
            correct += 1

    accuracy = correct / total
    print(f"Accuracy: {accuracy:.4f} ({correct}/{total})")
    return accuracy


def analyze_tflite_ops(tflite_path: Path):
    """Analyze operators used in TFLite model."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    ops_details = interpreter._get_ops_details()

    op_types = set()
    for op in ops_details:
        op_types.add(op['op_name'])

    print(f"\nOperators used in {tflite_path.name}:")
    for op in sorted(op_types):
        print(f"  - {op}")

    return sorted(op_types)


def main():
    parser = argparse.ArgumentParser(description="Convert Keras model to TFLite (FP32 and INT8)")
    parser.add_argument('--model', type=str, default='zylose_kws.keras', help='Input Keras model')
    parser.add_argument('--fp32-name', type=str, default='zylose_fp32.tflite', help='FP32 output name')
    parser.add_argument('--int8-name', type=str, default='zylose_int8.tflite', help='INT8 output name')
    args = parser.parse_args()

    keras_path = MODELS_DIR / args.model
    fp32_path = MODELS_DIR / args.fp32_name
    int8_path = MODELS_DIR / args.int8_name

    if not keras_path.exists():
        print(f"Error: Keras model not found at {keras_path}")
        return

    print(f"Loading Keras model from: {keras_path}")
    keras_model = tf.keras.models.load_model(keras_path)

    print("\n" + "="*60)
    print("CONVERTING TO FP32 TFLITE")
    print("="*60)
    fp32_model = convert_fp32(keras_model, fp32_path)

    print("\n" + "="*60)
    print("CONVERTING TO INT8 TFLITE")
    print("="*60)
    int8_model = convert_int8(keras_model, int8_path)

    X_test = np.load(DATASET_PROCESSED / "X_test.npy")
    X_test = X_test[..., np.newaxis].astype(np.float32)
    y_test = np.load(DATASET_PROCESSED / "y_test.npy")

    print("\n" + "="*60)
    print("VALIDATING MODELS")
    print("="*60)

    print("\n--- Keras Model (FP32) ---")
    keras_loss, keras_acc = keras_model.evaluate(X_test, y_test, verbose=0)
    print(f"Keras Accuracy: {keras_acc:.4f}")

    print("\n--- FP32 TFLite ---")
    fp32_acc = validate_tflite_model(fp32_path, X_test, y_test, 'float32')

    print("\n--- INT8 TFLite ---")
    int8_acc = validate_tflite_model(int8_path, X_test, y_test, 'int8')

    print("\n" + "="*60)
    print("OPERATOR ANALYSIS")
    print("="*60)
    fp32_ops = analyze_tflite_ops(fp32_path)
    int8_ops = analyze_tflite_ops(int8_path)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Keras FP32 Accuracy:    {keras_acc:.4f}")
    print(f"TFLite FP32 Accuracy:   {fp32_acc:.4f}")
    print(f"TFLite INT8 Accuracy:   {int8_acc:.4f}")
    print(f"FP32 Model Size:        {len(fp32_model)/1024:.1f} KB")
    print(f"INT8 Model Size:        {len(int8_model)/1024:.1f} KB")
    print(f"Compression Ratio:      {len(fp32_model)/len(int8_model):.2f}x")
    print(f"Accuracy Drop (Keras->INT8): {keras_acc - int8_acc:.4f}")

    results = {
        'keras_accuracy': float(keras_acc),
        'fp32_accuracy': float(fp32_acc),
        'int8_accuracy': float(int8_acc),
        'fp32_size_kb': len(fp32_model) / 1024,
        'int8_size_kb': len(int8_model) / 1024,
        'compression_ratio': len(fp32_model) / len(int8_model),
        'fp32_operators': fp32_ops,
        'int8_operators': int8_ops
    }

    with open(MODELS_DIR / "conversion_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    print("\nConversion complete!")


if __name__ == "__main__":
    main()