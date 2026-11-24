# Changelog

All notable changes to Tuna are documented here.

This project is currently in beta. Entries describe the development state and may include experimental functionality.

## [1.0.0-beta.1] - 2026-11-25

### Added
- Re-established the project foundation while preserving the existing Git repository and history.
- PySide6 desktop companion interface with compact and expanded views.
- Animated pixel-art avatar with multiple expressions and UI state-driven animation.
- Local Ollama provider integration.
- Configurable model selection through environment configuration.
- PostgreSQL persistence for conversations, messages and memories.
- Conversation restoration and memory management components.
- Background chat worker for model requests.
- Initial experimental voice-recognition foundation:
  - `sherpa-onnx` speaker embedding dependency.
  - Titanet speaker embedding model loaded successfully.
  - 192-dimensional speaker embeddings.
  - Microphone capture tested with `sounddevice` at 16 kHz on Apple Silicon macOS.

### Changed
- Updated the default tested local model to `qwen3:4b-instruct-2507-q4_K_M`.
- Refined Tuna's personality prompt to favour concise, calm, natural and resourceful responses.

### In progress
- Voice enrollment and speaker verification.
- Voice interaction integration with the desktop interface.

### Not included in this release
- Complete speech-to-text and text-to-speech pipeline.
- Wake-word detection.
- Cross-device memory synchronisation.
- A validated distributable macOS application wrapper.
