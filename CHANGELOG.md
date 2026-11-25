# Changelog

## 1.1.1 — Live voice and minimal interface

- Reworked the desktop UI with a rounded, dark iOS-inspired appearance.
- Replaced the earlier character frames with 16 new pixel-art frames featuring larger, more expressive eyes.
- Added live interim transcription in the message input using local streaming Sherpa-ONNX ASR.
- Added one-press-to-record / second-press-to-stop voice capture and automatic submission after speech endpoint detection.
- Fixed microphone handoff: the one-shot wake listener exits and releases the microphone before ASR starts.
- Added local macOS speech output with preferred female English voice selection and configurable rate.
- Tightened Gennie's system prompt, removed emoji from generated replies, and reduced default generation length/temperature.
- Prevented pytest from collecting the manual wake-word diagnostic script.

## 1.0.0-beta.2 — Project Gennie rebrand

- Replaced the Tuna mascot presentation with an original female genie character in pixel art.
- Added animation frames, expression sprites, a sprite atlas, pixel-art lamp and glow assets.
- Added EMERGING and RETURNING behavioural states.
- Added local Sherpa-ONNX wake-word worker and Gennie keyword setup script.
- Rebranded the desktop UI, personality prompt, Python package metadata and documentation.
- Added `GENNIE_*` configuration while retaining `TUNA_*` fallbacks.
- Kept existing PostgreSQL table names and stored data intact.

## Compatibility

`TunaBrain` remains an import alias for `GennieBrain`. Existing memory tables, `.env`, model files and local speaker profile are not removed.
