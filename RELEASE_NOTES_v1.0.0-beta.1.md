# Tuna v1.0.0-beta.1

**First beta milestone — local desktop companion foundation**

Tuna reaches its first beta milestone with a working desktop companion foundation, local model integration and persistent conversation storage.

## Highlights

- A compact PySide6 desktop companion with an animated pixel-art avatar.
- Expanded chat interface for conversations.
- Local inference through Ollama.
- Tested with `qwen3:4b-instruct-2507-q4_K_M`.
- PostgreSQL-backed conversation and memory components.
- Background processing for AI responses.
- Initial speaker-recognition groundwork using sherpa-onnx and a Titanet embedding model.
- Microphone capture validated on the development Mac.

## Experimental features

Voice is not yet a finished end-user feature. The embedding model loads and microphone capture works, but enrollment, speaker verification calibration and full voice interaction still need implementation and testing.

## Platform

The development environment validated so far is an Apple Silicon MacBook Air M1 with 8 GB RAM, macOS, Python 3.14, Ollama and PostgreSQL 18. Other platforms are not yet validated.

## Before installing

This is a developer-focused beta. Expect configuration work and incomplete features. Back up any important local database before changing application versions.

## What's next

The immediate focus is completing voice enrollment and speaker verification, then integrating push-to-talk and speech recognition into the existing desktop workflow.
