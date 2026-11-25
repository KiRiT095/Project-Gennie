#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${GENNIE_WAKE_MODEL_DIR:-$PROJECT_DIR/models/wakeword/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01}"
RAW="$PROJECT_DIR/models/wakeword/keywords_raw.txt"
OUT="${GENNIE_KEYWORDS_FILE:-$PROJECT_DIR/models/wakeword/keywords.txt}"

if [[ ! -f "$MODEL_DIR/tokens.txt" || ! -f "$MODEL_DIR/bpe.model" ]]; then
  echo "Missing GigaSpeech wake-word model files in: $MODEL_DIR" >&2
  exit 1
fi
mkdir -p "$(dirname "$OUT")"
printf 'GENNIE\nGENIE\nJENNY\n' > "$RAW"
command -v sherpa-onnx-cli >/dev/null 2>&1 || { echo "sherpa-onnx-cli is missing. Activate your venv and install sherpa-onnx." >&2; exit 1; }
sherpa-onnx-cli text2token \
  --tokens "$MODEL_DIR/tokens.txt" \
  --tokens-type bpe \
  --bpe-model "$MODEL_DIR/bpe.model" \
  "$RAW" "$OUT"
echo "Generated Gennie wake-word tokens: $OUT"
cat "$OUT"
