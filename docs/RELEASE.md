# Git release hygiene

This source ZIP intentionally excludes `.git/`, `.env`, model weights, voice profiles, recordings, caches and local migration backups. Extract it over your existing clone; preserve your `.env` and local `models/` folder.

Before committing:

```bash
python -m compileall -q app scripts
python -m pytest -q
git status --short
git diff --check
```

Never commit `.env`, `models/`, `voice_data/`, speaker profiles, recordings or database dumps.
