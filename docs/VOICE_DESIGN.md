# Voice interaction design

Voice is the intended primary interaction method, but this UI prototype does not yet access the microphone.

## Intended interaction

1. A local wake-word service detects the configured wake phrase.
2. Tuna opens or comes to the foreground and enters `LISTENING`.
3. Local speech-to-text produces a transcript shown below the avatar.
4. The brain processes the request.
5. Text-to-speech speaks the response while the response subtitle appears in Tuna's window.
6. Tuna returns to `IDLE`.

## Privacy and control requirements before always-on listening

- Ask for macOS microphone permission through the normal system prompt.
- Provide a visible microphone/listening indicator.
- Provide clear pause/mute and disable-wake-word controls.
- Prefer on-device wake-word detection and transcription where practical.
- Do not record or retain raw audio by default.
- Do not send audio to a network service unless the user explicitly selects that provider.
- Make microphone startup and shutdown part of a managed service lifecycle.

## Implementation order

1. Add a `VoiceService` interface with lifecycle methods and typed events.
2. Add push-to-talk recording as the first testable audio interaction.
3. Add local speech-to-text and connect transcript events to `show_user_transcription()`.
4. Add text-to-speech and connect subtitle events to `show_assistant_subtitle()`.
5. Add configurable local wake-word detection last, with explicit opt-in and pause controls.

Do not treat the display hooks as evidence that voice is already implemented.
