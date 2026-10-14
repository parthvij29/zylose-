#!/usr/bin/env python3
"""
Zylose NLP Intent & Action Classifier
-------------------------------------
Trains a Deep Neural Network (MLP) on acoustic voice transcripts to classify
user intents into 4 core functional domains:
  1. DEVICE_CONTROL   - Physical actuation (LED, Display, Motors)
  2. SYSTEM_TELEMETRY - Hardware metrics (CPU, RAM, Battery, Uptime)
  3. KNOWLEDGE_QUERY  - Open-ended AI / factual questions (ISRO, Science, ML)
  4. EMERGENCY_ABORT  - High-priority safety / abort commands
"""

import os
import joblib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ============================================================
#                      TRAINING DATASET
# ============================================================

RAW_DATA = [
    # 1. DEVICE_CONTROL
    ("turn on the led", "DEVICE_CONTROL"),
    ("turn off the led", "DEVICE_CONTROL"),
    ("switch on the light", "DEVICE_CONTROL"),
    ("switch off the light", "DEVICE_CONTROL"),
    ("blink the led", "DEVICE_CONTROL"),
    ("flash the light three times", "DEVICE_CONTROL"),
    ("turn off the oled screen", "DEVICE_CONTROL"),
    ("turn on the oled display", "DEVICE_CONTROL"),
    ("clear the screen", "DEVICE_CONTROL"),
    ("reset the display", "DEVICE_CONTROL"),
    ("activate the motor", "DEVICE_CONTROL"),
    ("stop the motor", "DEVICE_CONTROL"),
    ("open the valve", "DEVICE_CONTROL"),
    ("close the valve", "DEVICE_CONTROL"),
    ("enable the actuator", "DEVICE_CONTROL"),
    ("disable actuator", "DEVICE_CONTROL"),
    ("turn off the peripheral", "DEVICE_CONTROL"),
    ("set brightness to maximum", "DEVICE_CONTROL"),
    ("dim the screen", "DEVICE_CONTROL"),
    ("turn on relay", "DEVICE_CONTROL"),
    ("toggle relay switch", "DEVICE_CONTROL"),
    ("activate buzzer alert", "DEVICE_CONTROL"),
    ("mute buzzer", "DEVICE_CONTROL"),
    ("start fan cooling", "DEVICE_CONTROL"),
    ("stop fan", "DEVICE_CONTROL"),

    # 2. SYSTEM_TELEMETRY
    ("what is the battery percentage", "SYSTEM_TELEMETRY"),
    ("check battery level", "SYSTEM_TELEMETRY"),
    ("show battery status", "SYSTEM_TELEMETRY"),
    ("what is the cpu utilization", "SYSTEM_TELEMETRY"),
    ("check memory usage", "SYSTEM_TELEMETRY"),
    ("how much ram is free", "SYSTEM_TELEMETRY"),
    ("show available sram", "SYSTEM_TELEMETRY"),
    ("what is the device temperature", "SYSTEM_TELEMETRY"),
    ("check core temperature", "SYSTEM_TELEMETRY"),
    ("how long has the system been running", "SYSTEM_TELEMETRY"),
    ("show device uptime", "SYSTEM_TELEMETRY"),
    ("what is the wifi signal strength", "SYSTEM_TELEMETRY"),
    ("check connection latency", "SYSTEM_TELEMETRY"),
    ("show telemetry diagnostics", "SYSTEM_TELEMETRY"),
    ("system health report", "SYSTEM_TELEMETRY"),
    ("what is the inference processing time", "SYSTEM_TELEMETRY"),
    ("show tinyml latency", "SYSTEM_TELEMETRY"),
    ("display model stats", "SYSTEM_TELEMETRY"),
    ("how many detections today", "SYSTEM_TELEMETRY"),
    ("show inference count", "SYSTEM_TELEMETRY"),
    ("what is current clock speed", "SYSTEM_TELEMETRY"),
    ("get hardware diagnostics", "SYSTEM_TELEMETRY"),
    ("is the sensor working properly", "SYSTEM_TELEMETRY"),
    ("check microphone status", "SYSTEM_TELEMETRY"),
    ("report device status", "SYSTEM_TELEMETRY"),

    # 3. KNOWLEDGE_QUERY
    ("what is artificial intelligence", "KNOWLEDGE_QUERY"),
    ("explain machine learning", "KNOWLEDGE_QUERY"),
    ("what is deep learning", "KNOWLEDGE_QUERY"),
    ("how does a neural network work", "KNOWLEDGE_QUERY"),
    ("what is tinyml", "KNOWLEDGE_QUERY"),
    ("explain edge computing", "KNOWLEDGE_QUERY"),
    ("who is the chairman of isro", "KNOWLEDGE_QUERY"),
    ("tell me about chandrayaan", "KNOWLEDGE_QUERY"),
    ("what is the gaganyaan mission", "KNOWLEDGE_QUERY"),
    ("how do rocket engines work", "KNOWLEDGE_QUERY"),
    ("what is a satellite orbit", "KNOWLEDGE_QUERY"),
    ("who was vikram sarabhai", "KNOWLEDGE_QUERY"),
    ("what is the distance to mars", "KNOWLEDGE_QUERY"),
    ("tell me about the solar system", "KNOWLEDGE_QUERY"),
    ("what is quantum computing", "KNOWLEDGE_QUERY"),
    ("how does speech recognition work", "KNOWLEDGE_QUERY"),
    ("what are mfcc features", "KNOWLEDGE_QUERY"),
    ("who invented the esp32", "KNOWLEDGE_QUERY"),
    ("what is the weather today", "KNOWLEDGE_QUERY"),
    ("tell me a fun science fact", "KNOWLEDGE_QUERY"),
    ("who is albert einstein", "KNOWLEDGE_QUERY"),
    ("what is a black hole", "KNOWLEDGE_QUERY"),
    ("explain gravity in simple terms", "KNOWLEDGE_QUERY"),
    ("what is the speed of light", "KNOWLEDGE_QUERY"),
    ("how does gps work", "KNOWLEDGE_QUERY"),

    # 4. EMERGENCY_ABORT
    ("abort mission", "EMERGENCY_ABORT"),
    ("abort immediately", "EMERGENCY_ABORT"),
    ("emergency stop", "EMERGENCY_ABORT"),
    ("stop all operations", "EMERGENCY_ABORT"),
    ("halt the system right now", "EMERGENCY_ABORT"),
    ("kill all processes", "EMERGENCY_ABORT"),
    ("critical alert detected", "EMERGENCY_ABORT"),
    ("system failure shut down", "EMERGENCY_ABORT"),
    ("danger stop the motors", "EMERGENCY_ABORT"),
    ("emergency power cutoff", "EMERGENCY_ABORT"),
    ("trigger emergency protocol", "EMERGENCY_ABORT"),
    ("safety shutdown initiated", "EMERGENCY_ABORT"),
    ("abort launch sequence", "EMERGENCY_ABORT"),
    ("override and shut down", "EMERGENCY_ABORT"),
    ("immediate emergency brake", "EMERGENCY_ABORT"),
    ("threat detected stop", "EMERGENCY_ABORT"),
    ("catastrophic failure alert", "EMERGENCY_ABORT"),
    ("disengage all power immediately", "EMERGENCY_ABORT"),
    ("all systems stop", "EMERGENCY_ABORT"),
    ("panic stop", "EMERGENCY_ABORT"),
]

CLASSES = ["DEVICE_CONTROL", "SYSTEM_TELEMETRY", "KNOWLEDGE_QUERY", "EMERGENCY_ABORT"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

def plot_confusion_matrix(cm, classes, save_path):
    """Plot and save high-resolution confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=classes, yticklabels=classes,
           title='Zylose Intent Classifier: Confusion Matrix',
           ylabel='True Class Label',
           xlabel='Predicted Class Label')
    
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontweight="bold")
    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Plot Saved] {save_path}")

def plot_metrics(report_dict, classes, save_path):
    """Plot precision, recall, and f1-score comparison per class."""
    precisions = [report_dict[c]['precision'] for c in classes]
    recalls = [report_dict[c]['recall'] for c in classes]
    f1s = [report_dict[c]['f1-score'] for c in classes]

    x = np.arange(len(classes))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.bar(x - width, precisions, width, label='Precision', color='#3b82f6')
    ax.bar(x, recalls, width, label='Recall', color='#10b981')
    ax.bar(x + width, f1s, width, label='F1-Score', color='#8b5cf6')

    ax.set_ylabel('Score')
    ax.set_title('Evaluation Metrics per Intent Domain (Test Set)')
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=15)
    ax.set_ylim(0, 1.15)
    ax.legend(loc='lower right')
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for i in range(len(classes)):
        ax.text(x[i] - width, precisions[i] + 0.02, f"{precisions[i]:.2f}", ha='center', fontsize=8)
        ax.text(x[i], recalls[i] + 0.02, f"{recalls[i]:.2f}", ha='center', fontsize=8)
        ax.text(x[i] + width, f1s[i] + 0.02, f"{f1s[i]:.2f}", ha='center', fontsize=8)

    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Plot Saved] {save_path}")

def plot_training_loss(loss_curve, save_path):
    """Plot neural network training loss curve."""
    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)
    ax.plot(loss_curve, color='#ef4444', linewidth=2, label='Cross-Entropy Loss')
    ax.set_title('Neural Network Training Loss Curve')
    ax.set_xlabel('Epoch (Iterations)')
    ax.set_ylabel('Loss')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Plot Saved] {save_path}")

def main():
    print("=" * 65)
    print(" [TRAINING] ZYLOSE DEEP LEARNING NLP INTENT CLASSIFIER")
    print("=" * 65)

    texts = [item[0] for item in RAW_DATA]
    labels = [item[1] for item in RAW_DATA]

    print(f"Total samples: {len(texts)}")
    for c in CLASSES:
        print(f"  • {c:<20}: {labels.count(c)} samples")

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"\nSplit: {len(X_train)} Train | {len(X_test)} Test")

    # Feature Extraction: TF-IDF with Unigrams, Bigrams & Trigrams
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), sublinear_tf=True, max_features=1200)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Deep Neural Network (MLP: 2 Hidden Layers with Adam optimizer)
    print("\nTraining Deep Neural Network (MLP: 128 -> 64)...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        alpha=1e-4,
        max_iter=300,
        random_state=42,
        early_stopping=False
    )
    mlp.fit(X_train_vec, y_train)

    train_acc = mlp.score(X_train_vec, y_train)
    test_acc = mlp.score(X_test_vec, y_test)
    print(f"\nTraining Accuracy : {train_acc * 100:.2f}%")
    print(f"Test Set Accuracy : {test_acc * 100:.2f}%")

    # Predictions & Evaluation
    y_pred = mlp.predict(X_test_vec)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, zero_division=0)
    print("\nClassification Report:\n" + report_str)

    cm = confusion_matrix(y_test, y_pred, labels=CLASSES)

    # Save visual evaluation artifacts
    os.makedirs("results", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    cm_path = os.path.join("results", "intent_confusion_matrix.png")
    metrics_path = os.path.join("results", "intent_metrics_barchart.png")
    loss_path = os.path.join("results", "intent_training_loss.png")
    report_txt_path = os.path.join("results", "intent_classification_report.txt")

    plot_confusion_matrix(cm, CLASSES, cm_path)
    plot_metrics(report_dict, CLASSES, metrics_path)
    plot_training_loss(mlp.loss_curve_, loss_path)

    with open(report_txt_path, "w") as f:
        f.write("ZYLOSE INTENT CLASSIFIER EVALUATION REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Training Accuracy: {train_acc * 100:.2f}%\n")
        f.write(f"Test Accuracy    : {test_acc * 100:.2f}%\n\n")
        f.write(report_str)
    print(f"[Report Saved] {report_txt_path}")

    # Export Pipeline
    model_payload = {
        "vectorizer": vectorizer,
        "model": mlp,
        "classes": CLASSES
    }
    model_path = os.path.join("models", "intent_model.joblib")
    joblib.dump(model_payload, model_path)
    print(f"[Model Saved] {model_path}")

    # Interactive Verification Test
    print("\n" + "=" * 65)
    print(" [TEST] LIVE INFERENCE VERIFICATION")
    print("=" * 65)
    test_queries = [
        "turn on the green led right now",
        "how much ram is left on the device",
        "tell me how machine learning works",
        "emergency abort all motors stop",
        "what is the cpu temperature",
        "switch off the display screen",
        "who is the isro chairman"
    ]

    for q in test_queries:
        vec = vectorizer.transform([q])
        pred = mlp.predict(vec)[0]
        probs = mlp.predict_proba(vec)[0]
        conf = np.max(probs) * 100
        print(f" Query : \"{q}\"")
        print(f" -> Predicted Intent: [{pred}] (Confidence: {conf:.1f}%)\n")

if __name__ == "__main__":
    main()
