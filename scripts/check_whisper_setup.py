#!/usr/bin/env python3
"""Verify the local Whisper.cpp executable and model without opening the mic."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cli = os.getenv("GENNIE_WHISPER_CLI", "").strip() or shutil.which("whisper-cli") or shutil.which("whisper-cpp")
model_value = Path(os.getenv("GENNIE_WHISPER_MODEL", str(root / "models/stt/ggml-small.en-q5_1.bin"))).expanduser()
model = model_value if model_value.is_absolute() else root / model_value
print(f"whisper.cpp executable: {cli or 'NOT FOUND'}")
print(f"Whisper model: {model}")
if not cli:
    raise SystemExit("FAIL: install whisper.cpp with: brew install whisper-cpp")
if not model.is_file() or model.stat().st_size < 100_000_000:
    raise SystemExit("FAIL: Whisper Small model is missing or incomplete. Run: bash scripts/setup_voice.sh")
print(f"Model size: {model.stat().st_size / (1024 * 1024):.1f} MiB")
print("SUCCESS: Whisper is installed. The microphone was not opened.")
