#!/usr/bin/env python3
"""
Zylose Speech Urgency & Affective State Classifier (Model 3)
------------------------------------------------------------
Trains a Deep Neural Network (MLP) to detect the urgency and emotional stress
level of the user from voice transcriptions:
  1. CALM_NORMAL       - Standard operational commands and relaxed queries
  2. HIGH_URGENCY      - Panic, distress, critical emergency, danger warnings
  3. INQUIRING_CURIOUS - Investigative, exploratory, or puzzled inquiries
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
    # 1. CALM_NORMAL
    ("turn on the green led please", "CALM_NORMAL"),
    ("turn off the light", "CALM_NORMAL"),
    ("can you dim the display", "CALM_NORMAL"),
    ("switch on the room peripheral", "CALM_NORMAL"),
    ("clear the screen now", "CALM_NORMAL"),
    ("show me the device status", "CALM_NORMAL"),
    ("what time is it", "CALM_NORMAL"),
    ("how much battery is remaining", "CALM_NORMAL"),
    ("check memory usage please", "CALM_NORMAL"),
    ("system check is nominal", "CALM_NORMAL"),
    ("set brightness to fifty percent", "CALM_NORMAL"),
    ("play the confirmation tone", "CALM_NORMAL"),
    ("reset the counter to zero", "CALM_NORMAL"),
    ("display the welcome screen", "CALM_NORMAL"),
    ("everything is operating normally", "CALM_NORMAL"),
    ("good morning zylose", "CALM_NORMAL"),
    ("thank you for the assistance", "CALM_NORMAL"),
    ("turn on the small fan", "CALM_NORMAL"),
    ("read out the current temperature", "CALM_NORMAL"),
    ("toggle relay switch two", "CALM_NORMAL"),
    ("all systems look fine", "CALM_NORMAL"),
    ("status report is clear", "CALM_NORMAL"),
    ("switch to power saving mode", "CALM_NORMAL"),
    ("idle mode activated", "CALM_NORMAL"),

    # 2. HIGH_URGENCY
    ("stop right now immediately", "HIGH_URGENCY"),
    ("emergency abort mission", "HIGH_URGENCY"),
    ("danger fire detected in the lab", "HIGH_URGENCY"),
    ("halt all operations immediately", "HIGH_URGENCY"),
    ("critical failure in motor drive", "HIGH_URGENCY"),
    ("cut off all power quickly", "HIGH_URGENCY"),
    ("warning battery overheating", "HIGH_URGENCY"),
    ("emergency stop abort abort", "HIGH_URGENCY"),
    ("kill the main process right away", "HIGH_URGENCY"),
    ("system malfunction urgent help", "HIGH_URGENCY"),
    ("catastrophic failure impending", "HIGH_URGENCY"),
    ("danger stop the actuators now", "HIGH_URGENCY"),
    ("immediate emergency shut off", "HIGH_URGENCY"),
    ("safety hazard alert red", "HIGH_URGENCY"),
    ("disengage all power supplies fast", "HIGH_URGENCY"),
    ("pressure leak detected shut down", "HIGH_URGENCY"),
    ("overload warning cut the circuit", "HIGH_URGENCY"),
    ("panic stop everything", "HIGH_URGENCY"),
    ("rapid temperature spike abort", "HIGH_URGENCY"),
    ("emergency brake engage immediately", "HIGH_URGENCY"),
    ("danger runaway motor stop", "HIGH_URGENCY"),
    ("critical error shut it down now", "HIGH_URGENCY"),

    # 3. INQUIRING_CURIOUS
    ("what is the sun made of exactly", "INQUIRING_CURIOUS"),
    ("can you explain how machine learning works", "INQUIRING_CURIOUS"),
    ("who was the founder of isro", "INQUIRING_CURIOUS"),
    ("why is the sky blue during daytime", "INQUIRING_CURIOUS"),
    ("how do quantum computers process information", "INQUIRING_CURIOUS"),
    ("what is the difference between ram and sram", "INQUIRING_CURIOUS"),
    ("tell me about the chandrayaan landing site", "INQUIRING_CURIOUS"),
    ("how does a depthwise separable convolution work", "INQUIRING_CURIOUS"),
    ("i wonder what causes gravity in physics", "INQUIRING_CURIOUS"),
    ("could you tell me a fascinating astronomy fact", "INQUIRING_CURIOUS"),
    ("what makes rocket engines so powerful", "INQUIRING_CURIOUS"),
    ("how do satellites stay in geostationary orbit", "INQUIRING_CURIOUS"),
    ("can you tell me who albert einstein was", "INQUIRING_CURIOUS"),
    ("what is black hole event horizon", "INQUIRING_CURIOUS"),
    ("how does tinyml run on microcontrollers", "INQUIRING_CURIOUS"),
    ("explain neural network backpropagation simply", "INQUIRING_CURIOUS"),
    ("what is the distance between earth and moon", "INQUIRING_CURIOUS"),
    ("why do stars twinkle at night", "INQUIRING_CURIOUS"),
    ("how does speech recognition recognize phonemes", "INQUIRING_CURIOUS"),
    ("what is the speed of sound in air", "INQUIRING_CURIOUS"),
    ("could you explain quantum entanglement", "INQUIRING_CURIOUS"),
]

CLASSES = ["CALM_NORMAL", "HIGH_URGENCY", "INQUIRING_CURIOUS"]

def plot_confusion_matrix(cm, classes, save_path):
    """Plot and save high-resolution confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Reds)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=classes, yticklabels=classes,
           title='Zylose Urgency Classifier: Confusion Matrix',
           ylabel='True Urgency State',
           xlabel='Predicted Urgency State')
    
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", rotation_mode="anchor")

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

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.bar(x - width, precisions, width, label='Precision', color='#ef4444')
    ax.bar(x, recalls, width, label='Recall', color='#f59e0b')
    ax.bar(x + width, f1s, width, label='F1-Score', color='#8b5cf6')

    ax.set_ylabel('Score')
    ax.set_title('Evaluation Metrics per Urgency State (Test Set)')
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
    ax.plot(loss_curve, color='#dc2626', linewidth=2, label='Cross-Entropy Loss')
    ax.set_title('Urgency Classifier Training Loss Curve')
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
    print(" [TRAINING] ZYLOSE SPEECH URGENCY & AFFECTIVE CLASSIFIER")
    print("=" * 65)

    texts = [item[0] for item in RAW_DATA]
    labels = [item[1] for item in RAW_DATA]

    print(f"Total samples: {len(texts)}")
    for c in CLASSES:
        print(f"  * {c:<20}: {labels.count(c)} samples")

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"\nSplit: {len(X_train)} Train | {len(X_test)} Test")

    # Feature Extraction: TF-IDF with Unigrams, Bigrams & Trigrams
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), sublinear_tf=True, max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Deep Neural Network (MLP: 128 -> 64)
    print("\nTraining Deep Neural Network (MLP: 128 -> 64)...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        alpha=1e-4,
        max_iter=300,
        random_state=42
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

    # Save artifacts
    os.makedirs("results", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    cm_path = os.path.join("results", "urgency_confusion_matrix.png")
    metrics_path = os.path.join("results", "urgency_metrics_barchart.png")
    loss_path = os.path.join("results", "urgency_training_loss.png")
    report_txt_path = os.path.join("results", "urgency_classification_report.txt")

    plot_confusion_matrix(cm, CLASSES, cm_path)
    plot_metrics(report_dict, CLASSES, metrics_path)
    plot_training_loss(mlp.loss_curve_, loss_path)

    with open(report_txt_path, "w") as f:
        f.write("ZYLOSE SPEECH URGENCY CLASSIFIER EVALUATION REPORT\n")
        f.write("=" * 55 + "\n")
        f.write(f"Training Accuracy: {train_acc * 100:.2f}%\n")
        f.write(f"Test Accuracy    : {test_acc * 100:.2f}%\n\n")
        f.write(report_str)
    print(f"[Report Saved] {report_txt_path}")

    # Export Model
    model_payload = {
        "vectorizer": vectorizer,
        "model": mlp,
        "classes": CLASSES
    }
    model_path = os.path.join("models", "urgency_model.joblib")
    joblib.dump(model_payload, model_path)
    print(f"[Model Saved] {model_path}")

    # Verification Test
    print("\n" + "=" * 65)
    print(" [TEST] LIVE INFERENCE VERIFICATION")
    print("=" * 65)
    test_queries = [
        "emergency stop all motors immediately danger",
        "please turn on the green led light",
        "could you explain how black holes work",
        "danger critical overload shutdown fast",
        "how much ram is free on the device"
    ]

    for q in test_queries:
        vec = vectorizer.transform([q])
        pred = mlp.predict(vec)[0]
        probs = mlp.predict_proba(vec)[0]
        conf = np.max(probs) * 100
        print(f" Query : \"{q}\"")
        print(f" -> Predicted Urgency: [{pred}] (Confidence: {conf:.1f}%)\n")

if __name__ == "__main__":
    main()
