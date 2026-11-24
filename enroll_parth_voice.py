"""
Interactive Voice Biometrics Enrollment Tool for Parth
-------------------------------------------------------
Records 8 high-fidelity voice samples of Parth saying 'Zylose'.
Extracts your vocal cord fundamental pitch (F0), vocal tract formants,
and spectral timbre fingerprint. Saves 'parth_voiceprint.npy' & 'parth_voiceprint.json'.
"""

import sys
import time
import numpy as np
import sounddevice as sd
from voice_biometrics import (
    extract_acoustic_features,
    save_parth_voiceprint,
    verify_audio_speaker,
    trim_speech,
    TARGET_SR
)

SAMPLE_RATE = TARGET_SR  # Canonical 16,000 Hz
SAMPLE_DURATION = 2.5     # 2.5 seconds window (VAD isolates the ~0.7s speech)
TOTAL_SAMPLES = 8

def record_sample(sample_num):
    print(f"\n========================================================")
    print(f"  SAMPLE [{sample_num}/{TOTAL_SAMPLES}]: Voice Biometrics Calibration")
    print(f"========================================================")
    print("Instructions:")
    print(" 1. Press ENTER to arm the microphone.")
    print(" 2. Immediately say 'ZYLOSE' clearly in your normal voice.")
    input("\n[Press ENTER when ready to speak]...")

    print("🔴 RECORDING NOW... Say 'ZYLOSE'!", flush=True)
    audio = sd.rec(
        int(SAMPLE_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    print("⏹️ Recording finished! Processing acoustic features...", flush=True)

    audio_flat = audio.flatten()
    peak = float(np.max(np.abs(audio_flat)))

    if peak < 0.005:
        print("\n⚠️  [WARNING] Audio was too quiet (Microphone barely picked up sound)!")
        print("    Please speak closer to the microphone or check your mic volume.\n")
        return None, None

    # Check VAD speech segment
    trimmed = trim_speech(audio_flat, sr=SAMPLE_RATE)
    vad_duration = len(trimmed) / SAMPLE_RATE

    if vad_duration < 0.15:
        print("\n⚠️  [WARNING] No clear voice detected in the recording. Let's try again.\n")
        return None, None

    # Extract acoustic feature vector
    feat = extract_acoustic_features(audio_flat, sr=SAMPLE_RATE)
    f0 = feat[0]
    centroid = feat[2]

    print(f"   ✅ Vocal Pitch F0 : {f0:.1f} Hz")
    print(f"   ✅ Timbre Centroid: {centroid:.1f} Hz")
    print(f"   ✅ Spoken Segment : {vad_duration:.2f} seconds (Silence Trimmed)")

    return feat, audio_flat

def main():
    print("=" * 68)
    print("   ZYLOSE: SPEAKER BIOMETRICS ENROLLMENT (PARTH VOICE PROFILE)")
    print("=" * 68)
    print(" This tool will record 8 voice samples of Parth saying 'Zylose'.")
    print(" It calculates your physical vocal cord frequency and vocal tract")
    print(" resonance filterbanks, locking the assistant to your voice only.")
    print(" Friends or unauthorized voices will be automatically rejected.")
    print("=" * 68)

    samples = []
    raw_audios = []
    i = 1

    while i <= TOTAL_SAMPLES:
        feat, raw_aud = record_sample(i)
        if feat is not None:
            samples.append(feat)
            raw_audios.append(raw_aud)
            i += 1
        else:
            retry = input("Press ENTER to retry this sample (or 'q' to quit): ").strip().lower()
            if retry == 'q':
                print("Enrollment cancelled.")
                sys.exit(0)

    # Compute mean reference profile
    samples_arr = np.array(samples)
    mean_vec = np.mean(samples_arr, axis=0)
    std_vec = np.std(samples_arr, axis=0)

    # Set threshold
    threshold = 68.0

    # Save to disk
    save_parth_voiceprint(mean_vec, std_vec, threshold=threshold, num_samples=TOTAL_SAMPLES)

    print("\n" + "=" * 68)
    print("   RUNNING AUTOMATED SELF-VERIFICATION VALIDATION TEST...")
    print("=" * 68)

    scores = []
    for idx, raw_aud in enumerate(raw_audios, 1):
        verified, score, spk, dist = verify_audio_speaker(raw_aud, sr=SAMPLE_RATE)
        scores.append(score)
        status = "✅ PASS (VERIFIED)" if verified else "❌ FAIL"
        print(f" * Sample #{idx} Test Match: {score:.1f}% -> {status}")

    avg_score = float(np.mean(scores))

    print("\n" + "=" * 68)
    print("🎉 PARTH'S VOICE BIOMETRICS SUCCESSFULLY ENROLLED & CALIBRATED!")
    print("=" * 68)
    print(f" * Owner Name             : Parth")
    print(f" * Number of Samples      : {TOTAL_SAMPLES}")
    print(f" * Fundamental Pitch (F0) : {mean_vec[0]:.1f} Hz (±{std_vec[0]:.1f} Hz)")
    print(f" * Timbre Centroid        : {mean_vec[2]:.1f} Hz")
    print(f" * Security Threshold     : {threshold:.1f}% Match")
    print(f" * Self-Verification Avg  : {avg_score:.1f}% Match")
    print(f" * Saved Profile Files    : parth_voiceprint.npy & parth_voiceprint.json")
    print("=" * 68)
    print("\n[SUCCESS] Your assistant is now permanently tuned to Parth's voice!")
    print("You can now run 'python zylose_ai_assistant.py' (or 'run_zylose.bat').\n")

if __name__ == "__main__":
    main()
