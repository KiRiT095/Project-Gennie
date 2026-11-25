# Voice interaction design

## Ownership of the microphone

The wake-word and speech-recognition workers must never own the microphone at the same time.

- `WakeWordWorker` performs local keyword spotting while Gennie is in `SLEEPING`.
- On a match, it exits its input-stream context immediately. Its `finished` signal confirms the audio stream has been released.
- `SpeechRecognitionWorker` opens the same input device only after the wake worker has ended.
- The ASR worker emits partial text updates, then a final transcript when endpoint detection fires or the user presses Stop.
- After the response has been spoken and Gennie returns to `SLEEPING`, the wake worker is restarted.

The microphone button follows the same ownership rule: it first interrupts the wake listener, then starts streaming recognition. The button changes to Stop while a capture is active.

## Speech recognition

The app uses Sherpa-ONNX `OnlineRecognizer.from_transducer` with the int8 streaming Zipformer English model. It processes small 200 ms audio blocks and emits interim hypotheses as text changes. The model files are downloaded by `scripts/setup_asr_model.sh` and kept in `models/asr/`, which is excluded from Git.

The model is English-only. It can make mistakes, especially with noise, distant microphones, or accents not well represented by its training data. The visible interim transcript is intentionally editable before the final turn is sent.

## Speech output

On macOS, `SpeechOutputWorker` invokes the built-in `say` utility in a background thread. It prefers an installed English voice from the Ava/Samantha/Allison/Victoria family, but respects `GENNIE_TTS_VOICE` when that exact voice is installed. `GENNIE_TTS_RATE` controls pace. No voice audio is sent to a cloud service.

The installed voice catalogue differs by macOS release and downloaded voice packs; use `scripts/list_macos_voices.py` to inspect the local choices.

## Safety and privacy

Wake-word activation is not speaker authentication. A separate voice-verification step would be needed before using voice as an authorization factor for sensitive actions. The current voice flow is intended for conversational interaction, not account security.
