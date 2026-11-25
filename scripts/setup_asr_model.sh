#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_NAME="sherpa-onnx-streaming-zipformer-en-2023-06-26"
MODEL_ROOT="${GENNIE_ASR_MODEL_ROOT:-$PROJECT_DIR/models/asr}"
MODEL_DIR="$MODEL_ROOT/$MODEL_NAME"
ARCHIVE="$MODEL_ROOT/$MODEL_NAME.tar.bz2"
URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/$MODEL_NAME.tar.bz2"

if [[ -f "$MODEL_DIR/encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx" ]]; then
  echo "Streaming English ASR model is already installed: $MODEL_DIR"
  exit 0
fi

mkdir -p "$MODEL_ROOT"
echo "Downloading the local English streaming speech model (~70 MB)..."
curl --fail --location --retry 3 --output "$ARCHIVE" "$URL"
echo "Extracting model..."
tar -xjf "$ARCHIVE" -C "$MODEL_ROOT"
rm -f "$ARCHIVE"

for file in \
  encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx \
  decoder-epoch-99-avg-1-chunk-16-left-128.onnx \
  joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx \
  tokens.txt; do
  [[ -s "$MODEL_DIR/$file" ]] || { echo "Missing model file: $MODEL_DIR/$file" >&2; exit 1; }
done

echo "Installed local streaming ASR model: $MODEL_DIR"
echo "Audio recognition is English-only in this model and runs locally."
