"""Load Gennie's streaming ASR model without opening the microphone."""
from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    import sherpa_onnx

    root = Path(__file__).resolve().parents[1]
    default = root / "models" / "asr" / "sherpa-onnx-streaming-zipformer-en-2023-06-26"
    configured = Path(os.getenv("GENNIE_ASR_MODEL_DIR", str(default))).expanduser()
    model_dir = configured if configured.is_absolute() else root / configured

    files = {
        "encoder": model_dir / "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
        "decoder": model_dir / "decoder-epoch-99-avg-1-chunk-16-left-128.onnx",
        "joiner": model_dir / "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
        "tokens": model_dir / "tokens.txt",
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        print("ASR model files are missing:")
        print("\n".join(f"  {item}" for item in missing))
        print("Run: bash scripts/setup_asr_model.sh")
        return 2

    print(f"sherpa-onnx: {getattr(sherpa_onnx, '__version__', 'unknown')}")
    print(f"ASR model: {model_dir}")
    print("Loading the Zipformer2 recognizer (microphone remains closed)...")
    recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(files["tokens"]),
        encoder=str(files["encoder"]),
        decoder=str(files["decoder"]),
        joiner=str(files["joiner"]),
        num_threads=2,
        sample_rate=16_000,
        feature_dim=80,
        enable_endpoint_detection=True,
        rule1_min_trailing_silence=2.0,
        rule2_min_trailing_silence=1.15,
        rule3_min_utterance_length=20.0,
        decoding_method="greedy_search",
        model_type="zipformer2",
        provider="cpu",
    )
    # Creating a stream confirms the recognizer is usable, but does not access audio.
    recognizer.create_stream()
    print("SUCCESS: Zipformer2 ASR recognizer loaded.")
    print("The microphone was not opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
