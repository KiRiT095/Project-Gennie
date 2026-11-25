#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "No .env found. Copy selected settings from .env.example when you create one."
  exit 0
fi

BACKUP_DIR="$HOME/Library/Application Support/Gennie/config-backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/.env.$(date +%Y%m%d-%H%M%S).bak"
cp -p "$ENV_FILE" "$BACKUP_FILE"

python3 - "$ENV_FILE" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
updates = {
    "GENNIE_WAKE_THRESHOLD": "0.22",
}
add_if_missing = {
    "GENNIE_TTS_ENABLED": "true",
    "GENNIE_TTS_RATE": "174",
}

def set_value(key: str, value: str, *, replace_existing: bool) -> None:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    matches = [i for i, line in enumerate(lines) if pattern.match(line)]
    if matches:
        if replace_existing:
            for index in matches:
                lines[index] = f"{key}={value}"
    else:
        lines.append(f"{key}={value}")

for key, value in updates.items():
    set_value(key, value, replace_existing=True)
for key, value in add_if_missing.items():
    set_value(key, value, replace_existing=False)

path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
PY

echo "Updated voice defaults without changing database or model credentials."
echo "A private .env backup was saved outside the Git repository: $BACKUP_FILE"
