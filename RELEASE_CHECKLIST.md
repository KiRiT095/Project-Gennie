# Project Gennie 1.1.0 Release Checklist

## Code and tests
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m compileall -q app scripts`.
- [ ] Confirm `.env`, `.git`, `models/`, databases and local voice profiles are not included in release archives.

## Desktop UI
- [ ] Check the rounded dark window on the Mac display.
- [ ] Confirm Gennie's eye expressions, emergence and return animations.
- [ ] Confirm transcript text appears live in the input field.

## Voice
- [ ] Check microphone selection with `python scripts/list_macos_voices.py` and system microphone settings.
- [ ] Confirm the wake listener exits and releases the microphone after detecting Gennie.
- [ ] Confirm ASR updates interim text and submits the final transcript.
- [ ] Confirm the manual mic button starts/stops capture.
- [ ] Confirm TTS uses the preferred installed English voice.

## Existing data
- [ ] Confirm the existing `.env` is retained.
- [ ] Confirm PostgreSQL conversations and memories are still readable.
- [ ] Confirm the existing local speaker profile is untouched.
