# Project Gennie

A local-first desktop AI companion with a lamp-to-genie presence, expressive pixel-art character, and optional two-way voice chat.

## What this build does

- A compact lamp/character presence that expands into a rounded, dark, iOS-inspired conversation window.
- Updated 16-frame Gennie pixel-art animation with larger, more expressive eyes.
- Local Sherpa-ONNX wake-word detection for **“Gennie”**.
- After a wake-word match, the wake listener closes its microphone stream before the speech recognizer opens the device.
- Local Whisper Small English speech recognition (`whisper.cpp`, quantised model) with automatic silence detection and local transcription.
- A microphone button for manual voice input; silence ends each utterance automatically, and a second press can finish early.
- Local macOS speech output. The voice selector prefers Ava when installed, then Samantha and other available English voices. The selected voice and speaking rate can be configured.
- Existing Ollama chat, PostgreSQL conversation history and long-term memory are retained.
- No cloud speech service is used by the included voice path.

## Voice flow

1. While Gennie is resting in the lamp, the wake-word listener processes microphone audio locally.
2. When it detects “Gennie” (the keyword list includes phonetic spelling aliases), the wake thread exits and releases the microphone.
3. The genie emerges into a small voice HUD. The recognizer records one utterance and detects the end from silence.
4. Whisper Small transcribes the recording locally; the transcript appears in a compact user bubble and is sent to the local Ollama brain.
5. Gennie displays a floating reply subtitle and speaks using the selected macOS system voice.
6. After speaking, Gennie automatically listens for the next prompt. If no one speaks before the listening timeout, she returns to the lamp and rearms the wake listener.

Click the microphone button to start a voice turn manually. Silence ends the utterance; the button can also stop capture early. Voice conversations stay in a compact HUD with separate user and Gennie bubbles rather than opening the full chat history.

## Requirements

- macOS for the built-in `say` speech output.
- Python 3.11 or newer.
- Ollama and the configured local model for AI replies.
- PostgreSQL for persistent history and memory (text chat can remain usable if PostgreSQL is offline).
- Sherpa-ONNX for wake-word detection; whisper.cpp, sounddevice and NumPy for local speech recognition.

## Install / update

Keep your existing `.env`, `.git`, `models/`, and local voice enrollment data. Do not overwrite credentials or database configuration with `.env.example`.

```bash
source ~/.venv/bin/activate
python -m pip install -e '.[voice,dev]'
```

Install the local Whisper.cpp runtime and **Whisper Small English Q5_1** model once:

```bash
bash scripts/setup_voice.sh
```

The quantised model is approximately 190 MB and is downloaded into `models/stt/`, which is ignored by Git. Whisper runs locally on the Mac; the wake-word detector remains Sherpa-ONNX and is not replaced. The English-only model is intended for English speech, including English spoken with an Indian accent; it is not a Hinglish model.

Keep your existing wake-word model and `keywords.txt` in `models/wakeword/`. The Whisper setup does not regenerate or replace them. Check the rest of the project setup with:

```bash
python scripts/check_gennie_setup.py
```

The keyword setup includes `GENNIE`, `GENIE` and `JENNY` token aliases because speech recognition models may represent the same spoken name using different English spellings. A lower wake threshold can improve sensitivity but can also increase false activations; adjust it cautiously.

## macOS voice

Gennie uses the built-in macOS `say` speech service. The app chooses an installed English voice, preferring Ava, then Samantha and other available voices. To inspect the voices installed on your Mac:

```bash
python scripts/list_macos_voices.py
```

For a richer voice, open **System Settings → Accessibility → Spoken Content → System Voice → Manage Voices** and install an enhanced voice you like. Then set its exact name in `.env` with `GENNIE_TTS_VOICE`. For example:

```dotenv
GENNIE_TTS_ENABLED=true
GENNIE_TTS_VOICE=Ava
GENNIE_TTS_RATE=174
```

Voice names vary by macOS version and installed voice packs. The app falls back to an installed English voice if the configured name is unavailable.

## Configuration

Copy individual settings from `.env.example` only when needed. Existing `TUNA_MODEL`, `TUNA_OLLAMA_URL` and `TUNA_DATABASE_URL` variables remain supported as fallbacks.

Useful voice settings:

```dotenv
GENNIE_WAKE_ENABLED=true
GENNIE_WAKE_THRESHOLD=0.22
GENNIE_MIC_DEVICE=
GENNIE_WHISPER_MODEL=models/stt/ggml-small.en-q5_1.bin
GENNIE_VOICE_MAX_SECONDS=20
GENNIE_VOICE_END_SILENCE=1.15
GENNIE_VOICE_START_TIMEOUT=12
GENNIE_TTS_ENABLED=true
GENNIE_TTS_VOICE=
GENNIE_TTS_RATE=174
GENNIE_IDLE_TIMEOUT_MS=45000
```

Leave `GENNIE_MIC_DEVICE` blank to use the macOS default input device. When no index is specified, Gennie prefers a recognisable built-in MacBook microphone (rather than an iPhone Continuity microphone), then falls back to the system default. Set it to a device index only when you want to override that choice.

## Launch

```bash
python main.py
```

Right-click the compact character for the app menu. Click the character to open the conversation. The mic button starts/stops voice input; alternatively say “Gennie” while she is resting in the lamp. Voice sessions automatically listen for your next prompt after Gennie finishes speaking. Voice mode uses a small transcript/subtitle HUD rather than opening the full conversation log.

## Privacy and limitations

- Wake-word detection and speech recognition run locally; the included voice pipeline does not upload audio.
- The wake listener is active only while the app is open and Gennie is resting. It releases the mic before speech capture.
- Whisper Small English is English-only. Recognition quality still depends on microphone quality, distance, noise and accent; it is not designed for code-switching into Hindi.
- Wake-word detection does not verify who is speaking. The previously enrolled speaker profile is not yet used as a gate for every voice command.
- macOS speech output uses the voices installed on the user's Mac. Voice timbre and availability therefore vary by system.

## Data compatibility

Existing PostgreSQL tables (`tuna_conversations`, `tuna_messages`, `tuna_memories`) and legacy `TUNA_*` environment variables remain supported. No database rename, deletion or migration is performed. Keep `.env`, model weights and personal voice data out of Git.

## Tests

```bash
python -m pytest -q
python -m compileall -q app scripts
```
