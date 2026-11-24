# Roadmap

## Genesis — Core
- [x] State machine with validated transitions
- [x] Startup lifecycle
- [x] Unit tests for core state transitions

## Companion UI
- [x] Compact character-first window
- [x] Expanded conversation/history view
- [x] Hide text input in compact mode
- [x] State-driven pixel-art expressions
- [x] Temporary subtitle and transcription display hooks
- [x] Remove always-visible state label and instruction prompts
- [x] Hide empty dialogue bubbles
- [x] Add idle bob/blink and state-aware motion
- [ ] Verify sizing, animation feel, and drag behaviour on the user's Mac

## Voice — next major milestone
- [ ] Voice service interface and lifecycle
- [ ] Microphone permission and visible listening indicator
- [ ] Push-to-talk prototype
- [ ] Local speech-to-text
- [ ] Local text-to-speech
- [ ] Wake-word detection (explicit opt-in, mute/disable controls)

## Brain and memory
- [ ] Design replaceable brain/provider interface
- [ ] Connect a local model after interface design
- [ ] Design persistent memory schema and portability strategy
- [ ] Permissioned capability system; no arbitrary model shell access
