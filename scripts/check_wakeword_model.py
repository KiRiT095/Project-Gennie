"""Load the wake-word model without opening the microphone."""
from pathlib import Path
import os
import sherpa_onnx
from app.voice.wake_word import build_keyword_spotter

root = Path(__file__).resolve().parents[1]
model_dir = Path(os.getenv(
    "GENNIE_WAKE_MODEL_DIR",
    str(root / "models/wakeword/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"),
)).expanduser()
keywords = Path(os.getenv(
    "GENNIE_KEYWORDS_FILE", str(root / "models/wakeword/keywords.txt")
)).expanduser()
print("sherpa-onnx:", getattr(sherpa_onnx, "__version__", "unknown"))
print("model directory:", model_dir)
print("keywords file:", keywords)
spotter = build_keyword_spotter(model_dir, keywords)
stream = spotter.create_stream()
print("SUCCESS: Zipformer2 wake-word model loaded.")
print("The microphone was not opened.")
