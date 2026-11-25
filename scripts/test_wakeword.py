"""Standalone local wake-word test for Tuna."""

from pathlib import Path

import sounddevice as sd
import sherpa_onnx


ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    ROOT
    / "models"
    / "wakeword"
    / "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"
)

SAMPLE_RATE = 16000
DEVICE_INDEX = 3
CHUNK_DURATION = 0.1
BLOCK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


def main():
    files = {
        "tokens": MODEL_DIR / "tokens.txt",
        "encoder": MODEL_DIR / "encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "decoder": MODEL_DIR / "decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "joiner": MODEL_DIR / "joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "keywords_file": ROOT / "models" / "wakeword" / "keywords.txt",
    }

    for name, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {name}: {path}")

    print("Loading Tuna's wake-word detector...")

    spotter = sherpa_onnx.KeywordSpotter(
        tokens=str(files["tokens"]),
        encoder=str(files["encoder"]),
        decoder=str(files["decoder"]),
        joiner=str(files["joiner"]),
        keywords_file=str(files["keywords_file"]),
        num_threads=2,
        sample_rate=SAMPLE_RATE,
        feature_dim=80,
        max_active_paths=4,
        keywords_score=1.0,
        keywords_threshold=0.25,
        num_trailing_blanks=1,
        provider="cpu",
    )

    stream = spotter.create_stream()

    print("\nTuna wake-word detection is active.")
    print('Say "Tuna" near your MacBook microphone.')
    print("Press Ctrl+C to stop.\n")

    with sd.InputStream(
        device=DEVICE_INDEX,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_SIZE,
    ) as microphone:

        while True:
            samples, overflowed = microphone.read(BLOCK_SIZE)

            if overflowed:
                print("Microphone buffer overflow; audio may have been skipped.")

            stream.accept_waveform(SAMPLE_RATE, samples.reshape(-1))

            while spotter.is_ready(stream):
                spotter.decode_stream(stream)

            result = spotter.get_result(stream)

            if result:
                print(f'\nTUNA DETECTED: "{result}"')
                print("Listening for the next wake word...\n")
                spotter.reset_stream(stream)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWake-word listener stopped.")
    except Exception as exc:
        print(f"\nWake-word error: {exc}")
        raise
