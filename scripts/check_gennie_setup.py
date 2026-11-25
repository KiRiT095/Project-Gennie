"""Check local Gennie assets and wake-word/streaming-ASR model files."""
from pathlib import Path
import os

root = Path(__file__).resolve().parents[1]
wake_dir = Path(os.getenv(
    "GENNIE_WAKE_MODEL_DIR",
    str(root / "models/wakeword/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"),
)).expanduser()
asr_dir = Path(os.getenv(
    "GENNIE_ASR_MODEL_DIR",
    str(root / "models/asr/sherpa-onnx-streaming-zipformer-en-2023-06-26"),
)).expanduser()
if not wake_dir.is_absolute():
    wake_dir = root / wake_dir
if not asr_dir.is_absolute():
    asr_dir = root / asr_dir

keyword_file = Path(os.getenv("GENNIE_KEYWORDS_FILE", str(root / "models/wakeword/keywords.txt"))).expanduser()
if not keyword_file.is_absolute():
    keyword_file = root / keyword_file

checks = {
    "Gennie pixel sprite sheet": root / "assets/gennie/gennie_spritesheet.png",
    "lamp idle sprite": root / "assets/gennie/lamp_idle.png",
    "lamp glow sprite": root / "assets/gennie/lamp_glow.png",
    "wake-word keyword file": keyword_file,
    "wake encoder": wake_dir / "encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
    "wake decoder": wake_dir / "decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
    "wake joiner": wake_dir / "joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
    "streaming ASR encoder": asr_dir / "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
    "streaming ASR decoder": asr_dir / "decoder-epoch-99-avg-1-chunk-16-left-128.onnx",
    "streaming ASR joiner": asr_dir / "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
    "streaming ASR tokens": asr_dir / "tokens.txt",
}
missing = []
for name, path in checks.items():
    exists = path.is_file()
    print(("OK  " if exists else "MISS") + f" {name}: {path}")
    if not exists:
        missing.append(name)

if missing:
    print("\nSome local model assets are missing. Wake-word setup and streaming ASR will not both be available until their model files are installed.")
    print("ASR: bash scripts/setup_asr_model.sh")
    print("Wake word: keep the local model in models/wakeword/ and run bash scripts/configure_gennie_wakeword.sh")
