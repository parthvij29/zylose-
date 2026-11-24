# Team Work Distribution & 1-Minute Pitch Guide

**Project:** Zylose — Embedded On-Device Edge AI Voice Assistant  
**Institution:** Bennett University, SCSET  
**Evaluation:** AIML Laboratory Capstone Presentation  

---

## 1. Formal Work Distribution

| Team Member | Roll Number | Primary Responsibilities & Contributions |
| :--- | :--- | :--- |
| **Parth Vij** *(Team Lead)* | `S24CSEU1616` | **TinyML Core, Hardware Interfacing & Voice Biometrics:**<br>• Model 1 (1D-CNN INT8 Keyword Spotting) architecture & quantization.<br>• Model 2 (Acoustic Voice Biometrics & Speaker Verification Engine).<br>• Hardware interfacing: ESP32 I2S (INMP441 MEMS mic) and I2C (SSD1306 OLED).<br>• System integration, audio capture pipelines, and power optimization. |
| **Prashant Mangal** | `S24CSEU1615` | **Speech Processing & NLP Intent Classification:**<br>• Model 3 (Acoustic ASR Speech-to-Text Transcriber pipeline).<br>• Model 4 (Deep MLP Semantic Intent Classifier: 1200 TF-IDF $\to$ 128 $\to$ 64 $\to$ 4).<br>• Training dataset curation, categorical cross-entropy loss convergence.<br>• Multi-class confusion matrix validation and phoneme acoustic modeling. |
| **Prince Randhwa** | `S24CSEU1603` | **Affective Safety Modeling & Full-Stack Telemetry:**<br>• Model 5 (Speech Urgency & Stress Neural MLP for panic detection).<br>• Hardware safety cutoff integration (`CMD:ABORT` trigger within 3.9ms).<br>• Real-time Next.js 15 Edge Telemetry Dashboard with live state synchronization.<br>• Empirical research visualizations (ROC curves, loss graphs, quantization benchmarks). |

---

## 2. In-Person Presentation Strategy (How to Present to Ma'am)

### Opening Setup:
* Stand together confidently in order: **Parth $\to$ Prashant $\to$ Prince**.
* Keep the hardware sitting on the table with the OLED screen facing Ma'am, and have the laptop open to the Dashboard at `http://localhost:3000`.
* Total pitch time: **3 minutes (1 minute per person)** followed by the live demo.

---

### PERSON 1: PARTH VIJ (S24CSEU1616) — The Problem, Edge AI & Voice Biometrics
> **Timer:** ~60 Seconds  
> **Goal:** Hook Ma'am immediately, establish that everything runs on the ESP32 chip, and introduce the security feature.

**What to Say (Word-for-Word):**

> *"Good morning, Ma'am! Today, my teammates Prashant, Prince, and I are presenting **Zylose** — an on-device Edge AI voice assistant running entirely on this dual-core ESP32 microcontroller.*
> 
> *Traditional assistants like Alexa or Siri send raw audio to cloud servers. This causes high latency, severe privacy risks, and fails if the internet drops. We solved this by bringing the entire AI pipeline on-chip.*
> 
> *My primary focus was on **Model 1: Keyword Spotting** and **Model 2: Voice Biometrics**. For Model 1, we trained a 1D Convolutional Neural Network on 13 MFCC audio features. Using representative INT8 Post-Training Quantization, we compressed the model by 4x — down to just **37.4 Kilobytes** — achieving a **42-millisecond wake-up time** and **98.6% validation accuracy**.*
> 
> *To prevent unauthorized activations, I implemented **Model 2: Speaker Voice Biometrics**. Zylose extracts physical vocal cord invariants — including fundamental pitch and vocal tract harmonics. If anyone other than me tries to say 'Zylose', the similarity threshold fails, the OLED displays 'ACCESS DENIED', and the command is dropped.*
> 
> *Now, I’ll hand over to Prashant to explain our acoustic speech recognition and neural intent pipeline."*

---

### PERSON 2: PRASHANT MANGAL (S24CSEU1615) — Speech ASR & NLP Intent Classifier
> **Timer:** ~60 Seconds  
> **Goal:** Demonstrate solid Machine Learning fundamentals, TF-IDF vector space, and classification metrics.

**What to Say (Word-for-Word):**

> *"Thank you, Parth. Good morning, Ma'am!*
> 
> *Once Parth's voice is verified, the system transitions into conversational perception, which is where my models execute.*
> 
> *First, **Model 3: Acoustic ASR** transcribes the user's spoken question into text tokens under a low **4.2% Word Error Rate** using Connectionist Temporal Classification on Core 0.*
> 
> *Next, **Model 4: The Semantic Intent Classifier** analyzes the transcribed sentence. Rather than simple keyword matching, we extract a **1,200-dimensional TF-IDF feature vector** capturing unigram and bigram semantic relationships. This vector is fed into a **Deep Multi-Layer Perceptron** structured with 128 and 64 hidden nodes.*
> 
> *The model classifies the intent into four operational categories: Device Control, Emergency Abort, System Telemetry, and Knowledge Query. Trained with Adam optimization and categorical cross-entropy loss, it converges smoothly to **97.8% accuracy** with an inference latency of just **4.8 milliseconds**.*
> 
> *I’ll now pass it over to Prince to discuss our affective safety detector and live edge telemetry."*

---

### PERSON 3: PRINCE RANDHWA (S24CSEU1603) — Affective Safety, Interlocks & Live Telemetry
> **Timer:** ~60 Seconds  
> **Goal:** Show off safety actuation, full-stack engineering, and smoothly invite Ma'am into the live demonstration.

**What to Say (Word-for-Word):**

> *"Thank you, Prashant. Good morning, Ma'am!*
> 
> *In real-world robotics and smart systems, safety is paramount. That is why we integrated **Model 5: An Affective Urgency & Stress Detector**.*
> 
> *This neural classifier constantly monitors acoustic tension and distress phrasing. If high urgency or panic is detected, the model initiates a hardware safety interlock within **3.9 milliseconds** — disengaging the actuator via GPIO 4 and halting operations instantly with an emergency cutoff.*
> 
> *To visualize and benchmark this multi-model architecture, I developed the **Zylose Edge Telemetry Dashboard** you see on the screen. It features zero cloud delay, displays real-time confidences across all 5 models, and includes an interactive empirical evaluation suite showcasing our ROC-AUC curve of **0.992**, loss convergence plots, and confusion matrices.*
> 
> *At the same time, all data is mirrored in hardware on this physical **128 by 64 I2C OLED display**.*
> 
> *We would now love to give you a live demonstration of Zylose in action!"*

---

## 3. Quick Tips for High Marks
1. **Never read from paper:** Memorize the 4-5 bullet points in your speech and talk naturally.
2. **Body Language:** Point to the hardware when Parth talks about the chip, point to the OLED when Prashant talks about transcription, and point to the Dashboard screen when Prince talks about telemetry.
3. **Pacing:** Speak at a calm, conversational speed. One minute per person is plenty of time when you don't rush.
