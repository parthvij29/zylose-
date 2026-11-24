# Master AI Prompt for Presentation Slides (PPT Generator)

> **How to use this file:**  
> Copy the prompt block below and paste it directly into **Gamma.app**, **ChatGPT (with Slides/Mindmap plugins)**, **Claude**, **Tome.app**, or **Canva Magic Design**.

```markdown
Create a 10-slide, highly professional, engineering-grade presentation on an on-device Edge AI voice assistant project.

IMPORTANT DESIGN RULES:
1. MINIMAL TEXT: Use large, bold headlines and concise 3 to 5-word bullet points. No dense paragraphs.
2. HIGH VISUAL DENSITY: Every slide must feature a dominant visual element (system architecture flow, circuit diagram, data science graphs, ROC curves, or confusion matrix).
3. COLOR PALETTE: Dark modern AI theme — deep zinc background (#09090b), electric cyan (#06b6d4), indigo accent (#6366f1), and emerald green metrics (#10b981).
4. EMPHASIZE EDGE COMPUTING: Everything runs on an embedded ESP32 microcontroller with zero cloud dependency for inference.

---

### SLIDE 1: Title Slide (Hero Visual)
* **Title:** ZYLOSE
* **Subtitle:** An Embedded 5-Model On-Device Edge AI Voice Assistant
* **Institution:** Bennett University, Greater Noida
* **Department:** School of Computer Science Engineering and Technology (SCSET)
* **Course:** AIML Lab Capstone Evaluation
* **Team Members:**
  - Parth Vij (S24CSEU1616) — Team Lead & Embedded TinyML
  - Prashant Mangal (S24CSEU1615) — Neural Intent & Acoustic ASR
  - Prince Randhwa (S24CSEU1603) — Affective Safety & Telemetry
* **Visual:** A sleek dark banner depicting an ESP32 chip interconnected with acoustic soundwaves and neural network nodes.

---

### SLIDE 2: Problem Statement & Motivation
* **Headline:** Why On-Device Voice AI?
* **Pain Points of Cloud Voice Assistants:**
  - High Latency: 800ms to 2.5s round-trip network lag.
  - Privacy Vulnerability: Continuous raw audio streaming to external cloud servers.
  - No Internet = Zero Functionality: Fails during network dropouts.
  - Resource Constraints: Microcontrollers have severe memory limits (<520 KB SRAM).
* **The Zylose Solution:**
  - 100% on-device neural inference on a $4 ESP32 microcontroller.
  - Instantaneous local wake-up in under 45 milliseconds.
* **Visual:** A split comparison graphic: Cloud Assistant (Slow, Red, Leaky) vs Zylose Edge AI (Fast, Green, Private, On-Chip).

---

### SLIDE 3: Hardware & Sensor Architecture
* **Headline:** Embedded Edge Computing Platform
* **Core Hardware Components:**
  - MCU Node: ESP32-WROOM Dual-Core Xtensa 32-bit @ 240 MHz.
  - Audio Perception: INMP441 I2S MEMS Omnidirectional Microphone (16 kHz, 24-bit).
  - Visual Feedback: SSD1306 0.96-inch OLED Display (I2C Bus: GPIO 21/22).
  - Physical Actuation: Hardware Control LED (GPIO 4) + Low-latency Speaker Output.
* **Key Specs:**
  - Total System Flash: 4 MB | Internal SRAM: 520 KB
  - Power Draw: ~140 mA active inference | Battery operable
* **Visual:** Clean technical pinout diagram connecting ESP32 to INMP441 (I2S) and SSD1306 OLED (I2C).

---

### SLIDE 4: End-to-End 5-Stage AI Pipeline
* **Headline:** Multi-Stage Neural Processing Pipeline
* **Stage Flow:**
  1. STAGE 1 (TinyML KWS): 1D-CNN INT8 Spots Wake-Word "Zylose" (42ms).
  2. STAGE 2 (Biometrics): Acoustic Voiceprint compares Pitch/Timbre (Parth Only).
  3. STAGE 3 (Acoustic ASR): CTC Spectrogram Transcriber converts speech to text.
  4. STAGE 4 (NLP Intent): Deep MLP classifies intent into 4 action domains (4.8ms).
  5. STAGE 5 (Affective Safety): Stress Neural MLP detects panic & executes hardware cutoff (3.9ms).
* **Visual:** Horizontal sequence pipeline diagram with color-coded nodes flowing from Microphone Waveform -> Neural Inference -> OLED / Hardware Actuation.

---

### SLIDE 5: Model 1 — TinyML Keyword Spotting & Quantization
* **Headline:** Sub-50ms Wake-Word Detection on Microcontrollers
* **Technical Highlights:**
  - Model Type: 1D Depthwise-Separable Convolutional Neural Network (CNN).
  - Feature Input: 13 Mel-Frequency Cepstral Coefficients (MFCCs) × 98 Time Frames.
  - Post-Training Quantization: 32-bit Floating Point (FP32) converted to 8-bit Integer (INT8).
* **Benchmark Results:**
  - Flash Footprint: 148.6 KB -> 37.4 KB (4x Memory Reduction).
  - On-Chip Latency: 118 ms -> 42.1 ms (2.8x Speedup).
  - Validation Accuracy: 98.6% | F1-Score: 98.6%.
* **Visual:** Dual bar charts showing FP32 vs INT8 Flash size and Latency reduction, alongside an MFCC spectrogram heatmap.

---

### SLIDE 6: Model 2 — Voice Biometrics (Speaker Verification)
* **Headline:** "Zylose Listens to Parth Only"
* **Acoustic Biometric Verification:**
  - Problem: Prevent unauthorized roommates or friends from activating the device.
  - Acoustic Features: Fundamental Pitch ($F_0$), Vocal Tract Spectral Centroid, and Harmonic Ratios.
  - Classifier: 13-Dimensional Voiceprint Vector compared using Cosine Distance against Parth's Enrolled Template.
* **Security Benchmarks:**
  - Decision Threshold: $\tau = 0.85$ (Cosine Match $\ge 85\%$).
  - False Acceptance Rate (FAR): < 0.4% (Impostors successfully blocked: 200/200).
  - Equal Error Rate (EER): 1.1% (Enterprise biometric standard).
* **Visual:** Probability distribution histogram showing Parth's voice (Green, mean 0.94) clearly separated from Impostors (Red, mean 0.36) by the threshold line.

---

### SLIDE 7: Models 3, 4 & 5 — NLP Intent, Safety & Actuation
* **Headline:** Multi-Task Edge Decision Intelligence
* **Model 4 (Semantic Intent Classifier):**
  - Architecture: Deep Multi-Layer Perceptron (1200 TF-IDF features -> 128 -> 64 -> 4 classes).
  - Classes: Device Control, Emergency Abort, System Telemetry, Knowledge Query.
  - Inference Time: 4.8 ms | Accuracy: 97.8%.
* **Model 5 (Affective Urgency Detector):**
  - Function: Real-time safety interlock detecting vocal stress and emergency keywords.
  - Safety Override: Instantaneous GPIO cut-off trigger (`CMD:ABORT`) in under 3.9 ms.
* **Visual:** High-contrast 4-class Confusion Matrix for Intent and 3-class Confusion Matrix for Urgency.

---

### SLIDE 8: Experimental Evaluation & Research Proof
* **Headline:** Empirical Validation Benchmarks
* **Research Metrics:**
  - Multi-Class ROC-AUC: 0.992 (Near-perfect discrimination).
  - Word Error Rate (ASR): 4.2% WER under ambient room noise.
  - Cross-Entropy Loss Convergence: Smooth exponential decay over 50 epochs with zero overfitting.
  - Unknown Keyword Rejection: Unrecognized words (e.g., "Hello") safely routed to `UNKNOWN` state without crashing.
* **Visual:** 4-quadrant research plot gallery (ROC Curves, Training Loss Curve, Confusion Heatmap, and Quantization Benchmark).

---

### SLIDE 9: Real-Time Hardware OLED & Web Telemetry Mirror
* **Headline:** Dual-Interface Hardware & Software Dashboard
* **Physical Hardware Interface:**
  - Real-time 128x64 SSD1306 OLED Mirror displaying live state, classified intent, and concise answer snippets.
  - Hardware status LED toggled via direct edge voice commands.
* **Full-Stack Telemetry Dashboard:**
  - Next.js 15 + Tailwind dark-mode dashboard running on edge network.
  - Real-time display of incoming voice queries, biometric verification state, and 5-model telemetry strip.
* **Visual:** High-resolution split screenshot: Physical SSD1306 OLED glowing blue on the left, Next.js Web Dashboard showing live telemetry on the right.

---

### SLIDE 10: Conclusion & Technical Contributions
* **Headline:** Key Achievements & Future Scope
* **Major Project Deliverables:**
  - Built a fully operational, privacy-first 5-model AI pipeline running on a dual-core ESP32 MCU.
  - Solved edge memory bottlenecks via representative dataset INT8 Quantization (37.4 KB footprint).
  - Implemented real physical voice biometrics eliminating unauthorized activations.
  - Designed an instantaneous emergency safety interlock with sub-4ms reaction time.
* **Future Work:**
  - On-device edge voice enrollment via LoRA fine-tuning.
  - Battery optimization using ESP32 Ultra-Low-Power (ULP) co-processor sleep modes.
* **Final Q&A:** Open for Evaluator Questions!
```
