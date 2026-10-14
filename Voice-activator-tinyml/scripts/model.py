#!/usr/bin/env python3
"""
Model architecture for TinyML keyword spotting.
Very small CNN with depthwise separable convolutions for ESP32-S3.
"""

import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from config import (
    EXPECTED_FRAMES, NUM_MFCC, NUM_CLASSES, CLASS_LABELS,
    RANDOM_SEED
)


def create_model(input_shape: tuple, num_classes: int = NUM_CLASSES) -> tf.keras.Model:
    """Create the TinyML KWS model."""
    tf.keras.utils.set_random_seed(RANDOM_SEED)

    inputs = layers.Input(shape=input_shape, name="input")

    x = layers.Conv2D(
        filters=16,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        use_bias=False,
        kernel_regularizer=regularizers.l2(1e-4),
        name="conv1"
    )(inputs)
    x = layers.BatchNormalization(name="bn1")(x)
    x = layers.ReLU(name="relu1")(x)

    x = layers.DepthwiseConv2D(
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        use_bias=False,
        depthwise_regularizer=regularizers.l2(1e-4),
        name="dw_conv1"
    )(x)
    x = layers.BatchNormalization(name="bn2")(x)
    x = layers.ReLU(name="relu2")(x)

    x = layers.DepthwiseConv2D(
        kernel_size=(3, 3),
        strides=(2, 2),
        padding="same",
        use_bias=False,
        depthwise_regularizer=regularizers.l2(1e-4),
        name="dw_conv2"
    )(x)
    x = layers.BatchNormalization(name="bn3")(x)
    x = layers.ReLU(name="relu3")(x)

    x = layers.GlobalAveragePooling2D(name="gap")(x)

    x = layers.Dense(
        16,
        activation="relu",
        kernel_regularizer=regularizers.l2(1e-4),
        name="dense1"
    )(x)
    x = layers.Dropout(0.1, name="dropout")(x)

    outputs = layers.Dense(
        num_classes,
        activation="softmax",
        name="output"
    )(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="zylose_kws")
    return model


def print_model_info(model: tf.keras.Model, input_shape: tuple):
    """Print model summary and size estimates."""
    print("\n" + "="*60)
    print("MODEL ARCHITECTURE")
    print("="*60)
    model.summary()

    total_params = model.count_params()
    trainable_params = sum([tf.keras.backend.count_params(w) for w in model.trainable_weights])
    non_trainable_params = total_params - trainable_params

    print(f"\nTotal parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Non-trainable parameters: {non_trainable_params:,}")

    fp32_size_kb = (total_params * 4) / 1024
    int8_size_kb = (total_params * 1) / 1024

    print(f"\nEstimated FP32 model size: {fp32_size_kb:.1f} KB")
    print(f"Estimated INT8 model size: {int8_size_kb:.1f} KB")

    dummy_input = tf.random.normal((1,) + input_shape)
    _ = model(dummy_input)

    print(f"\nInput shape: {input_shape}")
    print(f"Output shape: {model.output_shape}")
    print("="*60)


def get_model_size_mb(model: tf.keras.Model) -> float:
    """Get model size in MB."""
    var_sizes = [tf.keras.backend.count_params(v) * 4 for v in model.trainable_variables]
    var_sizes += [tf.keras.backend.count_params(v) * 4 for v in model.non_trainable_variables]
    return sum(var_sizes) / (1024 * 1024)


if __name__ == "__main__":
    input_shape = (EXPECTED_FRAMES, NUM_MFCC, 1)
    model = create_model(input_shape)
    print_model_info(model, input_shape)