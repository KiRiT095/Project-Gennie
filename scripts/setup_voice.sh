#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v brew >/dev/null 2>&1 || { echo "Install Homebrew first: https://brew.sh" >&2; exit 1; }
brew list whisper-cpp >/dev/null 2>&1 || brew install whisper-cpp
if ! python -c 'import numpy, sounddevice, sherpa_onnx' >/dev/null 2>&1; then
  python -m pip install -e '.[voice]'
fi

mkdir -p models/stt
MODEL="models/stt/ggml-small.en-q5_1.bin"
if [[ ! -s "$MODEL" ]]; then
  echo "Downloading Whisper Small English (quantised, approximately 190 MB)..."
  curl -fL --retry 3 --retry-delay 2 \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en-q5_1.bin" \
    -o "$MODEL.tmp"
  mv "$MODEL.tmp" "$MODEL"
fi

CLI="$(command -v whisper-cli || command -v whisper-cpp || true)"
[[ -n "$CLI" ]] || { echo "whisper.cpp was installed but whisper-cli is not on PATH." >&2; exit 1; }
[[ -s "$MODEL" ]] || { echo "Whisper model download failed: $MODEL" >&2; exit 1; }
echo "Whisper.cpp: $CLI"
echo "Whisper model ready: $MODEL"
echo "Existing wake-word model, keyword file, .env, and database were not modified."
echo "Grant microphone access to Terminal/VS Code in System Settings → Privacy & Security → Microphone."
