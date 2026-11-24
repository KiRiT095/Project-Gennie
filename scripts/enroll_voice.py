import json
import os
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import sherpa_onnx

# Configuration
DEVICE = 3
SAMPLE_RATE = 16000
DURATION = 6
MODEL = Path("models/speaker/nemo_en_titanet_small.onnx")

PROFILE_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Tuna"
    / "voice"
)
PROFILE_FILE = PROFILE_DIR / "profile.json"

SENTENCES = [
    "Hello Tuna. This is my voice, and I am enrolling it.",
    "I want you to recognise me whenever I speak to you.",
    "A good solution is usually simple, reliable, and practical.",
    "Let's see how well you can recognise my voice.",
]

def extract_embedding(extractor, audio):
    stream = extractor.create_stream()
    stream.accept_waveform(
        SAMPLE_RATE,
        audio.astype(np.float32)
    )
    stream.input_finished()

    embedding = np.asarray(
        extractor.compute(stream),
        dtype=np.float32
    )

    norm = np.linalg.norm(embedding)
    if norm == 0:
        raise ValueError("The model returned an empty embedding.")

    return embedding / norm

def main():
    if not MODEL.exists():
        raise FileNotFoundError(f"Speaker model not found: {MODEL}")

    print("Loading speaker recognition model...")

    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(
        sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(MODEL),
            num_threads=2,
            debug=False,
        )
    )

    embeddings = []

    print("\nTuna voice enrollment")
    print("====================")
    print("Use your MacBook Air microphone.")
    print("Speak naturally. Avoid music and background noise.")

    for index, sentence in enumerate(SENTENCES, start=1):
        while True:
            print(f"\nSample {index}/4")
            print(f'Read: "{sentence}"')
            input("Press Enter when ready...")

            print("Recording...")
            audio = sd.rec(
                int(DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                device=DEVICE,
            )
            sd.wait()
            audio = audio.flatten()

            rms = float(np.sqrt(np.mean(audio ** 2)))
            peak = float(np.max(np.abs(audio)))

            print(f"Recording level — RMS: {rms:.5f}, Peak: {peak:.5f}")

            if rms < 0.005:
                print("Recording too quiet. Let's try again.")
                continue

            if peak > 0.98:
                print("Recording may be clipping. Let's try again.")
                continue

            try:
                embedding = extract_embedding(extractor, audio)
                embeddings.append(embedding)
                print("Sample accepted.")
                break
            except Exception as error:
                print(f"Embedding extraction failed: {error}")
                return

            time.sleep(0.5)

    # Average the four normalised embeddings.
    profile = np.mean(embeddings, axis=0)
    profile_norm = np.linalg.norm(profile)

    if profile_norm == 0:
        raise ValueError("Could not create a valid voice profile.")

    profile = profile / profile_norm

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(PROFILE_DIR, 0o700)

    data = {
        "version": 1,
        "model": MODEL.name,
        "sample_rate": SAMPLE_RATE,
        "embedding_dimension": int(extractor.dim),
        "enrollment_samples": len(embeddings),
        "embedding": profile.tolist(),
    }

    PROFILE_FILE.write_text(json.dumps(data))
    os.chmod(PROFILE_FILE, 0o600)

    print("\nVoice enrollment successful.")
    print(f"Profile saved locally: {PROFILE_FILE}")
    print("Raw recordings were not saved.")
    print("Next: test recognition against your enrolled profile.")

if __name__ == "__main__":
    main()
