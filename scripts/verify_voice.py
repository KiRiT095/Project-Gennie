
import json
import os
from pathlib import Path

from app.voice.audio_devices import select_input_device

import numpy as np
import sounddevice as sd
import sherpa_onnx

MODEL = Path("models/speaker/nemo_en_titanet_small.onnx")
SUPPORT_DIR = Path.home() / "Library" / "Application Support"
LEGACY_PROFILE = SUPPORT_DIR / "Tuna" / "voice" / "profile.json"
GENNIE_PROFILE = SUPPORT_DIR / "Gennie" / "voice" / "profile.json"
PROFILE = LEGACY_PROFILE if LEGACY_PROFILE.exists() else GENNIE_PROFILE

DEVICE = None
SAMPLE_RATE = 16000
DURATION = 6


def main():
    if not MODEL.exists():
        raise FileNotFoundError(f"Model missing: {MODEL}")

    if not PROFILE.exists():
        raise FileNotFoundError(f"Voice profile missing: {PROFILE}")

    profile = json.loads(PROFILE.read_text())
    enrolled = np.asarray(profile["embedding"], dtype=np.float32)

    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(
        sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(MODEL),
            num_threads=2,
            debug=False,
        )
    )

    if len(enrolled) != extractor.dim:
        raise ValueError("Voice profile dimension does not match model.")

    print("\nGennie speaker verification test")
    print("===============================")
    print("Speak naturally for six seconds.")
    input("Press Enter to start recording...")

    device = select_input_device(sd, os.getenv("GENNIE_MIC_DEVICE", ""))
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=device,
    )
    sd.wait()
    audio = audio.flatten()

    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))

    print(f"\nRecording RMS: {rms:.5f}")
    print(f"Recording peak: {peak:.5f}")

    if rms < 0.005 or peak > 0.98:
        print("Recording quality check failed. Try again.")
        return

    stream = extractor.create_stream()
    stream.accept_waveform(SAMPLE_RATE, audio)
    stream.input_finished()

    if not extractor.is_ready(stream):
        print("Not enough usable speech in recording.")
        return

    embedding = np.asarray(
        extractor.compute(stream),
        dtype=np.float32,
    )

    norm = np.linalg.norm(embedding)
    if norm == 0:
        print("Invalid embedding.")
        return

    embedding /= norm

    similarity = float(np.dot(enrolled, embedding))

    print("\nVerification result")
    print("-------------------")
    print(f"Cosine similarity: {similarity:.4f}")
    print("This is a measurement, not an authentication decision.")
    print("We need genuine-speaker and other-speaker samples to calibrate it.")


if __name__ == "__main__":
    main()
