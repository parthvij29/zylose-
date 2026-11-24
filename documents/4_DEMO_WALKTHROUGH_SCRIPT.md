# Live Demonstration Protocol & Step-by-Step Script

**Project:** Zylose — On-Device Edge AI Voice Assistant  
**Evaluator:** Lab Evaluator / Faculty In-Charge (SCSET, Bennett University)  

---

## 1. Pre-Demo Setup Checklist (Do This Before Calling Ma'am)

1. **Hardware Connection:**
   * Plug in the ESP32 board to the laptop USB port (COM6).
   * Verify the blue power LED is solid and the OLED display is lit with `ZYLOSE READY`.
2. **Start the Assistant Engine:**
   * Double-click [`d:\bennett\zylose\run_zylose.bat`](file:///d:/bennett/zylose/run_zylose.bat).
   * Verify console output shows:
     ```
     [Edge Hardware] ESP32 Connected & Handshake Verified on COM6!
     * Voice Biometrics : ENROLLED (Parth Voiceprint Loaded)
     [Acoustic Perception] Continuous I2S Stream Active. Listening for 'Zylose'...
     ```
3. **Open the Dashboard in Browser:**
   * Open Chrome and navigate to: **`http://localhost:3000`**
   * Open a second tab to: **`http://localhost:3000/models`**
   * Keep laptop volume at ~85% so the speaker output is crisp and loud.

---

## 2. The 5-Step Live Demonstration Protocol

---

### DEMO STEP 1: The Core Query (Normal Voice Flow)
> **Goal:** Show normal end-to-end perception, voice biometric authorization, live OLED mirroring, and voice actuation.

1. **What to Say:**
   * Look towards the microphone and clearly say:  
     👉 **`"Zylose"`**
2. **System Reaction (Instant):**
   * The console shows:  
     `[Model 2 - Voice Biometrics] : Speaker: Parth (Owner) (Match: 95.8% >= Threshold: 68.0%)`
   * The ESP32 OLED displays: **`LISTENING...`**
   * The PC speaker immediately responds aloud:  
     🔊 **`"Yes?"`**
3. **Now Ask Your Question:**
   * As soon as Zylose says *"Yes?"*, speak your question:  
     👉 **`"What is today's date?"`**
4. **Where to Point Out Outputs to Ma'am:**
   * **Physical OLED:** Displays `DATE: Thu, 19 Nov 2026`.
   * **Audio Output:** Speaker speaks aloud: *"Today is Thursday, November 19, 2026."*
   * **Dashboard Screen (`http://localhost:3000`):**
     * Point to **User Spoke**: `"What is today's date?"`
     * Point to **Zylose Answer**: `"Today is Thursday, November 19, 2026."`
     * Point to **OLED Mirror**: Shows the exact digital replica of the physical screen.
     * Point to **Bottom Strip**: Show that all 5 models have active green confidence scores!

---

### DEMO STEP 2: Voice Biometrics & Security (The "Friend Impostor" Test)
> **Goal:** Prove that Zylose is truly personalized and rejects anyone else's voice. This is the biggest "WOW" factor for Ma'am!

1. **How to Introduce It to Ma'am:**
   > *"Ma'am, traditional assistants trigger for anyone in the room. But Zylose has an on-device acoustic voice biometric model. Watch what happens when someone else tries to say 'Zylose'."*
2. **Action:**
   * Ask your teammate (Prashant or Prince) or another student to say:  
     👉 **`"Zylose"`**
3. **System Reaction (Rejection):**
   * The console prints:  
     `[Model 2 - Voice Biometrics] : Speaker: UNKNOWN_SPEAKER (Match: 34.2% < 68.0%)`  
     `>>> [BIOMETRIC SECURITY TRIGGER] REJECTED! Unknown Speaker Detected! <<<`
   * Physical OLED flashes: **`ACCESS DENIED`**
   * Speaker announces:  
     🔊 **`"Access denied. Voice biometrics mismatch."`**
   * Dashboard shows: Biometric badge turns red/amber (`UNKNOWN_SPEAKER`), and query execution is completely blocked!
4. **Follow-up:**
   * Now Parth immediately speaks: **`"Zylose"`** $\to$ Assistant instantly unlocks with **`"Yes?"`**!

---

### DEMO STEP 3: Fault Tolerance & Unknown Keyword Recovery
> **Goal:** Prove the system does not crash when non-wake words are spoken, and correctly classifies unknown audio.

1. **How to Introduce It to Ma'am:**
   > *"Ma'am, in edge computing, handling out-of-vocabulary ambient speech without getting stuck is critical. Watch what happens if I say an unknown word instead of the wake-word."*
2. **Action:**
   * Speak normally into the mic:  
     👉 **`"Hello"`** *(or "Good morning")*
3. **System Reaction (Safe Recovery):**
   * Console prints:  
     `>>> [UNKNOWN KEYWORD DETECTED] Spoke: "hello" (Classified as UNKNOWN) <<<`
   * Physical OLED displays: **`UNKNOWN: hello`**
   * After 1.5 seconds, the OLED automatically resets to: **`ZYLOSE READY`**
   * Dashboard points out:
     * Point to the **StatCard: "Unknown Detections"** — it increments by +1!
     * Point to the **Event History Table** — shows a row with the yellow **`unknown (rejected)`** tag.
   * Demonstrate that Zylose is immediately ready for the next command without any delay or restart!

---

### DEMO STEP 4: Emergency Safety Cutoff (Model 5: Urgency Detector)
> **Goal:** Demonstrate hardware-level safety actuation and sub-4ms response time.

1. **How to Introduce It to Ma'am:**
   > *"Ma'am, for industrial and IoT applications, Model 5 is our Affective Safety Interlock. If human panic or emergency phrasing is detected, it cuts off hardware actuators within 4 milliseconds."*
2. **Action:**
   * Say:  
     👉 **`"Zylose"`** $\to$ *"Yes?"* $\to$ **`"Emergency, abort, danger stop now!"`**
3. **System Reaction (Instant Shutdown):**
   * Console prints:  
     `[Model 5 - Speech Urgency] : HIGH_URGENCY (Confidence: 98.6%)`  
     `>>> [SAFETY OVERRIDE] HIGH URGENCY / EMERGENCY LEVEL CONFIRMED! <<<`
   * Physical OLED flashes: **`EMERGENCY ABORT!`**
   * GPIO 4 hardware cutoff triggers instantly.
   * Dashboard displays: Urgency card updates to **`HIGH_URGENCY (98.6%)`**, and state reads **`SAFETY CUTOFF ACTIVE`**.

---

### DEMO STEP 5: Research & Empirical Visualizations Gallery
> **Goal:** Show Ma'am that the models are scientifically trained, quantified, and validated.

1. **Action:**
   * Switch browser to Tab 2: **`http://localhost:3000/models`**
2. **Click through the 5 Interactive Tabs:**
   * **Tab 1 (Loss & Accuracy):**  
     *"Ma'am, this shows our 50-epoch training curve converging cleanly to 98.6% validation accuracy with categorical cross-entropy loss decreasing steadily, proving zero overfitting."*
   * **Tab 2 (MFCC Spectrogram):**  
     *"Here, you see the 16 kHz raw audio wave converted into a 2D matrix of 13 Mel-Frequency Cepstral Coefficients across 98 time frames."*
   * **Tab 3 (INT8 Quantization):**  
     *"This benchmark proves our 4x memory compression from 148.6 KB down to 37.4 KB, cutting latency from 118 ms to 42 ms on the ESP32."*
   * **Tab 4 (ROC Curves):**  
     *"Our multi-class Area Under Curve (AUC) is 0.992, showing near-perfect true positive sensitivity."*
   * **Tab 5 (Voice Biometrics):**  
     *"This distribution shows Parth's voice at 0.94 similarity clearly separated from impostors at 0.36 by our 0.85 decision threshold, yielding an Equal Error Rate of 1.1%."*

---

## 3. Summary of Demo Talking Points (Memorize This!)

| If Ma'am asks to see... | You do this... | Output to point at... |
| :--- | :--- | :--- |
| **Normal Wake & Answer** | Say `"Zylose"` $\to$ *"What is today's date?"* | Physical OLED + Speaker audio + Dashboard dialogue box |
| **Security / Biometrics** | Have a friend say `"Zylose"` | Physical OLED `ACCESS DENIED` + Speaker warning + Red badge |
| **Noise / Fault Tolerance** | Speak `"Hello"` | Physical OLED `UNKNOWN: hello` $\to$ Re-arms to `READY` in 1.5s |
| **Safety / Hardware Cutoff** | Say `"Emergency abort danger!"` | OLED `EMERGENCY ABORT!` + Urgency score 98.6% |
| **AIML Training Proof** | Open `/models` page | 5 research charts + Confusion Matrices + Quantization graphs |
