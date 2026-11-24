# Tuna Roadmap

This roadmap describes the intended direction. Items are goals, not promises or release guarantees.

## Current — v1.0.0-beta.1

Focus: establish a stable local desktop companion foundation.

- [x] Rebuild and preserve the existing project structure and Git history.
- [x] PySide6 desktop interface.
- [x] Compact character-first window and expanded chat view.
- [x] Animated avatar with expression states.
- [x] Local Ollama integration.
- [x] PostgreSQL persistence for conversations and memories.
- [x] Background chat processing.
- [x] Validate the Instruct model with Tuna's system personality.
- [x] Install and load the initial speaker embedding model.
- [x] Verify microphone capture on the development Mac.
- [ ] Complete voice enrollment.
- [ ] Implement and calibrate speaker verification.
- [ ] Integrate push-to-talk into the desktop interface.

## Next — voice interaction

- [ ] Reliable local speech-to-text.
- [ ] Connect verified speech input to the existing chat pipeline.
- [ ] Local text-to-speech.
- [ ] Avatar speaking animation synchronised with audio output.
- [ ] Clear controls for microphone access, enrollment and re-enrollment.
- [ ] Test false acceptance and false rejection behaviour.
- [ ] Add an explicit fallback to typed input.

## Later — companion experience

- [ ] Improve memory quality, retrieval and user control.
- [ ] Better conversation organisation and history management.
- [ ] Optional quick-response and deeper-reasoning modes.
- [ ] Improve startup, shutdown and error recovery.
- [ ] Package and validate a native macOS application.

## Long-term — multi-device Tuna

- [ ] Run an independent local AI runtime on each supported device.
- [ ] Keep Tuna's identity consistent across device-specific installations.
- [ ] Build secure, authenticated memory synchronisation.
- [ ] Add memory export, import and recovery.
- [ ] Explore additional bodies, including mobile and Raspberry Pi.

## Principles

1. Local-first by default.
2. Memory should be portable; the model and local tools should remain device-specific.
3. Keep the architecture understandable and modular.
4. Prefer simple solutions without compromising reliability or security.
5. Be transparent about experimental features and limitations.
