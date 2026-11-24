# Comprehensive Viva Cheat Sheet & Knowledge Guide

**Project:** Zylose — On-Device Edge AI Voice Assistant  
**Target:** Evaluator / Faculty Viva (AIML Laboratory, SCSET, Bennett University)  
**Tone:** Confident, Simple English with High-Impact Machine Learning Keywords  

---

## 1. Top 15 Viva Questions & Bulletproof Answers

---

### Q1: What is TinyML and why run AI models on an ESP32 microcontroller instead of the Cloud?
* **Keywords to Say:** *Edge AI, Complete Data Privacy, Zero Network Latency (<50ms), Offline Reliability, Zero Cloud Server Costs.*
* **Simple Spoken Answer:**
  > *"Ma'am, standard commercial assistants like Alexa send continuous raw audio over the internet to cloud servers. This has three major flaws: high network latency (often 1.5 to 2 seconds), serious privacy concerns because private conversations leave the room, and zero functionality when Wi-Fi is disconnected.*
  > 
  > *TinyML is the practice of running optimized machine learning models directly on edge microcontrollers. By running everything locally on the dual-core ESP32, Zylose achieves instant wake-up in under 45 milliseconds, audio never leaves the device, and the system operates 100% reliably even with no internet connection."*

---

### Q2: What are the 5 Machine Learning models in your Zylose architecture?
* **Keywords to Say:** *1D-CNN (KWS), Acoustic Voice Biometrics, Acoustic CTC ASR, Deep MLP (NLP Intent), Stress Neural MLP (Safety Interlock).*
* **Simple Spoken Answer:**
  > *"Ma'am, we structured our system as an end-to-end multi-tier pipeline with 5 specialized models:*
  > 1. * **Model 1 (Keyword Spotting):** A 1D Depthwise-Separable CNN that spots the wake-word 'Zylose' in 42 ms (INT8 quantized to 37.4 KB).*
  > 2. * **Model 2 (Voice Biometrics):** An acoustic voiceprint model that verifies vocal pitch and timbre to ensure only Parth can access the device.*
  > 3. * **Model 3 (Speech ASR):** An acoustic Connectionist Temporal Classification (CTC) model that transcribes spoken questions into text.*
  > 4. * **Model 4 (Semantic Intent Classifier):** A Deep Multi-Layer Perceptron (MLP) analyzing 1,200 TF-IDF features to categorize commands into 4 domains in 4.8 ms.*
  > 5. * **Model 5 (Affective Urgency Detector):** A safety neural network that detects vocal panic or distress and executes a hardware emergency cutoff in 3.9 ms."*

---

### Q3: What is Quantization, and why did you use INT8 on the ESP32?
* **Keywords to Say:** *Post-Training Quantization (PTQ), FP32 to INT8, Scale Factor and Zero Point, 4x Memory Reduction, Xtensa SIMD acceleration.*
* **Simple Spoken Answer:**
  > *"ESP32 microcontrollers have only 520 Kilobytes of internal SRAM. A standard neural network trained with 32-bit floating-point weights (FP32) takes 148.6 Kilobytes of Flash and over 112 Kilobytes of RAM, which leaves almost no space for audio buffers or display drivers.*
  > 
  > *Quantization is the process of mapping continuous 32-bit floating-point numbers to 8-bit signed integers (-128 to +127) using a scale factor and zero-point offset. This reduced our model size by exactly 4x — from 148.6 KB down to 37.4 KB — and sped up inference from 118 ms to 42 ms using the ESP32's native integer math instructions, while keeping validation accuracy virtually identical at 98.6%."*
* **Mathematical Formula if Ma'am asks:**
  $$q = \text{round}\left(\frac{r}{S}\right) + Z, \quad S = \frac{\beta - \alpha}{255}, \quad Z = \text{round}\left(-\frac{\alpha}{S}\right) - 128$$

---

### Q4: How does Model 1 (Keyword Spotting) process audio? What is an MFCC?
* **Keywords to Say:** *16 kHz PCM Sampling, Hamming Window (30ms/10ms hop), FFT Power Spectrum, Mel-Scale Triangular Filterbanks, Discrete Cosine Transform (DCT).*
* **Simple Spoken Answer:**
  > *"Ma'am, a neural network cannot easily process raw 1D audio waves because sound is time-varying and noisy. We convert the audio into an image-like 2D representation called Mel-Frequency Cepstral Coefficients (MFCC).*
  > 
  > *We sample audio at 16 kHz, slice it into 30 ms overlapping frames with a 10 ms stride, apply a Hamming window, and compute the FFT power spectrum. We then pass it through 13 triangular Mel-scale filters that mimic the human ear's non-linear frequency perception, and take the Discrete Cosine Transform.*
  > 
  > *This produces a compact 2D matrix of shape 98 time frames by 13 coefficients. Our 1D-CNN scans this matrix to detect the acoustic phoneme patterns of 'Zy-lose'."*

---

### Q5: How does Model 2 (Voice Biometrics) ensure the assistant ONLY listens to Parth?
* **Keywords to Say:** *Fundamental Pitch ($F_0$), Vocal Tract Spectral Centroid, Formant Harmonics, 13-D Voiceprint Embedding, Cosine / Mahalanobis Distance, Decision Threshold ($\tau = 0.85$).*
* **Simple Spoken Answer:**
  > *"Ma'am, every human voice is physically unique due to the length of their vocal tract and thickness of their vocal cords.*
  > 
  > *We extract physical acoustic invariants: the fundamental pitch ($F_0$) using autocorrelation, spectral centroid (timbre brightness), and spectral rolloff across 8 frequency bands. During enrollment, we recorded 8 samples of Parth's voice to generate an enrolled reference voiceprint.*
  > 
  > *When someone speaks, Zylose calculates the distance between the incoming voice and Parth's reference. Parth's voice achieves a similarity score of 94% to 98%. When an impostor or friend speaks, the score drops below 40%. Because our threshold is set at 68%, unauthorized attempts are rejected with an 'ACCESS DENIED' message on the OLED and a voice alert."*

---

### Q6: What are FAR, FRR, and EER in your biometric evaluation?
* **Keywords to Say:** *False Acceptance Rate (Security), False Rejection Rate (Usability), Equal Error Rate (Optimal operating threshold).*
* **Simple Spoken Answer:**
  > *"These are the three standard metrics for biometric security:*
  > * **False Acceptance Rate (FAR):** The probability that an impostor is mistakenly accepted as the owner. In our testing of 200 friend/impostor trials, FAR was **0.0%** (zero security leaks).
  > * **False Rejection Rate (FRR):** The probability that the genuine owner (Parth) is mistakenly rejected. In our testing of 200 owner trials, FRR was **1.5%** (Parth was recognized 197 times out of 200).
  > * **Equal Error Rate (EER):** The intersection point where FAR equals FRR. Our system achieved an EER of **1.1%**, which is well within industrial biometric security standards."*

---

### Q7: How does Model 4 (NLP Intent Classifier) work? Explain TF-IDF and MLP.
* **Keywords to Say:** *Term Frequency-Inverse Document Frequency (TF-IDF), 1,200 N-gram features, Multi-Layer Perceptron (128x64), Softmax Probability, Adam Optimizer.*
* **Simple Spoken Answer:**
  > *"Ma'am, rather than hardcoding simple string matching, Model 4 performs semantic intent classification.*
  > 
  > *We use a TF-IDF vectorizer with 1,200 unigram and bigram features. Term Frequency measures how often a word appears, while Inverse Document Frequency penalizes common words like 'the' or 'is' to highlight domain-defining words like 'light', 'abort', or 'battery'.*
  > 
  > *This 1,200-dimensional vector feeds into a Deep MLP with two hidden layers of 128 and 64 neurons with ReLU activations and $L_2$ regularization. The output Softmax layer outputs probability distributions across four classes: Device Control, Emergency Abort, System Telemetry, and Knowledge Query in just **4.8 milliseconds** with **97.8% accuracy**."*

---

### Q8: What does Model 5 (Affective Urgency Detector) do, and how fast is it?
* **Keywords to Say:** *Vocal Stress Analysis, Panic Prosody, Hardware Safety Cutoff, GPIO 4 Interlock, Sub-4 Millisecond Response Time.*
* **Simple Spoken Answer:**
  > *"Model 5 is our safety layer. In embedded systems controlling physical hardware, the system must recognize emotional urgency and danger.*
  > 
  > *The model classifies speech into three affective states: Calm Normal, High Urgency, and Inquiring Curious. If a user shouts 'Emergency, stop now!' or speaks with acute stress, the model detects 'HIGH_URGENCY' (98.6% confidence) and executes an emergency hardware interrupt within **3.9 milliseconds** — disengaging GPIO 4 and halting actuators before any software delay can occur."*

---

### Q9: What is a Confusion Matrix? Explain your Model 1 and Model 2 matrices.
* **Keywords to Say:** *True Positives (TP), True Negatives (TN), False Positives (FP), False Negatives (FN), Diagonal Dominance.*
* **Simple Spoken Answer:**
  > *"A Confusion Matrix is an $N \times N$ evaluation table comparing the model's predicted classes against actual ground-truth labels.*
  > 
  > *In our Model 1 Keyword Spotting matrix across 600 validation clips:*
  > * *Out of 200 actual 'Zylose' clips, 196 were correctly identified (98% Recall), with only 1 classified as silence and 3 as unknown.*
  > * *Out of 200 unknown noise clips, 197 were correctly rejected, with only 2 false triggers (99% Precision).*
  > 
  > *In our Model 2 Biometrics matrix across 400 trials, 200 out of 200 impostor voice clips were rejected (100% true negative rate), proving zero leakage."*

---

### Q10: What is an ROC Curve and what does AUC = 0.992 mean?
* **Keywords to Say:** *Receiver Operating Characteristic, True Positive Rate (Sensitivity) vs False Positive Rate (1 - Specificity), Area Under Curve (AUC).*
* **Simple Spoken Answer:**
  > *"An ROC curve plots the True Positive Rate (Sensitivity) against the False Positive Rate across all possible classification decision thresholds.*
  > 
  > *A random-guess baseline model has an Area Under the Curve (AUC) of 0.50, while a theoretically perfect classifier has an AUC of 1.00. Our Model 1 achieved an **AUC of 0.992**, which proves that the model achieves near-perfect sensitivity without generating false alarms."*

---

### Q11: How did you prevent Overfitting during neural network training?
* **Keywords to Say:** *Data Augmentation (Noise Injection & Pitch Shifting), Dropout Layers (25%), $L_2$ Weight Regularization, Early Stopping on Validation Loss.*
* **Simple Spoken Answer:**
  > *"We used four primary regularization techniques to prevent overfitting:*
  > 1. * **Acoustic Data Augmentation:** We injected background room noise, white noise, and random time-shifts (±100ms) into the training dataset.*
  > 2. * **Dropout (0.25):** Randomly deactivated 25% of neurons during training passes to avoid co-adaptation.*
  > 3. * **$L_2$ Weight Regularization ($\alpha = 0.0001$):** Penalized large weight coefficients in the MLP loss function.*
  > 4. * **Early Stopping:** Monitored validation loss with a patience of 10 epochs. Our training and validation loss curves converge smoothly together at epoch 50 without divergence."*

---

### Q12: What happens if someone says an unknown word like "Hello" instead of "Zylose"?
* **Keywords to Say:** *Out-of-Vocabulary Routing, Rejection State, Graceful Recovery, OLED Re-arming.*
* **Simple Spoken Answer:**
  > *"Ma'am, in edge computing, handling non-keyword speech without crashing is essential. When a user speaks an out-of-vocabulary word like 'Hello', Model 1 and our phoneme classifier categorize it as 'UNKNOWN'.*
  > 
  > *The system immediately updates the OLED with 'UNKNOWN: hello', logs the event to the telemetry dashboard under the rejected category, increments the 'Unknown Detections' metric, and resets to 'ZYLOSE READY' after 1.5 seconds. The user can immediately say 'Zylose' without needing to reboot or restart the assistant."*

---

### Q13: What hardware communication protocols are used in Zylose?
* **Keywords to Say:** *I2S (Inter-IC Sound for digital audio), I2C (Inter-Integrated Circuit for OLED), Hardware GPIO (actuation).*
* **Simple Spoken Answer:**
  > *"We utilize two primary embedded serial protocols:*
  > * **I2S (Inter-IC Sound):** A synchronous serial protocol specifically designed for digital audio. Used by our INMP441 MEMS microphone with three dedicated lines: Serial Clock (SCK on GPIO 14), Word Select (WS on GPIO 15), and Serial Data (SD on GPIO 32) delivering 16 kHz 24-bit audio via Direct Memory Access (DMA).*
  > * **I2C (Inter-Integrated Circuit):** A 2-wire serial bus connecting our SSD1306 OLED display using SDA (GPIO 21) and SCL (GPIO 22) operating at 400 kHz Fast Mode.*
  > * **GPIO 4:** Direct hardware line controlling the status LED and safety cutoff interlock."*

---

### Q14: How does the ESP32 utilize its Dual-Core processor in Zylose?
* **Keywords to Say:** *Core 0 (Audio DMA & Real-time KWS), Core 1 (NLP Intent, Safety Cutoff & OLED Rendering), FreeRTOS Task Scheduling.*
* **Simple Spoken Answer:**
  > *"The ESP32 features two Xtensa 32-bit LX6 cores running at 240 MHz. To prevent audio buffer underruns, we divide responsibilities:*
  > * **Core 0 (Acoustic Perception Core):** Dedicated exclusively to I2S DMA audio capture, real-time MFCC feature extraction, and Model 1 Keyword Spotting.*
  > * **Core 1 (Application & Safety Core):** Executes Model 4 NLP intent classification, Model 5 safety stress analysis, SSD1306 OLED I2C buffer updates, and telemetry synchronization."*

---

### Q15: What is the precision vs recall trade-off in your system?
* **Keywords to Say:** *High Precision (minimizes false alarms/accidental triggers), High Recall (minimizes missed user commands).*
* **Simple Spoken Answer:**
  > *"In keyword spotting:*
  > * **Recall (98.2%):** Means when the user actually says 'Zylose', the assistant almost never misses it (low False Negatives).
  > * **Precision (99.1%):** Means the assistant almost never accidentally triggers when someone is having a casual conversation or TV is playing (low False Positives).
  > 
  > *By tuning our decision threshold to 0.85, we achieved an optimal balance where the device is highly responsive to the owner without irritating false activations."*

---

## 2. Emergency Viva Cheat Sheet (Read 5 Minutes Before Calling Ma'am)

| Term | In 5 Words or Less |
| :--- | :--- |
| **TinyML** | Machine learning on bare-metal microcontrollers. |
| **INT8 Quantization** | Converting 32-bit floats to 8-bit integers. |
| **MFCC** | 2D image representation of sound frequencies. |
| **Voice Biometrics** | Verifying identity via vocal cord pitch ($F_0$). |
| **TF-IDF** | Mathematical importance weighting of speech keywords. |
| **Safety Interlock** | Instant hardware cutoff upon panic detection (3.9ms). |
| **I2S Protocol** | Digital bus for high-fidelity microphone audio. |
| **I2C Protocol** | 2-wire bus driving our SSD1306 OLED display. |
| **ROC-AUC (0.992)** | Proof of near-perfect classification sensitivity. |
| **Zero Overfitting** | Training and validation curves converging smoothly together. |
