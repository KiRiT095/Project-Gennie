# Project Gennie Architecture

```text
Desktop UI (PySide6)
  ├─ Pixel-art lamp/genie avatar and rounded conversation window
  ├─ Live transcript input and manual microphone button
  ├─ WakeWordWorker (one-shot background QThread)
  │    └─ Microphone → Sherpa-ONNX KeywordSpotter → wake event → release mic
  ├─ SpeechRecognitionWorker (background QThread)
  │    └─ Microphone → Sherpa-ONNX OnlineRecognizer → interim/final text
  └─ SpeechOutputWorker (background QThread)
       └─ macOS say → preferred installed English voice

GennieBrain → ChatProvider → local Ollama
      └─ Conversation → PostgreSQL store → MemoryManager
```

## Microphone handoff

Only one worker may own the microphone at a time. On a wake match, `WakeWordWorker` breaks out of its input-stream context and exits. The UI waits for the worker to finish before creating `SpeechRecognitionWorker`. The recognizer emits interim hypotheses to the input field, then a final transcript after endpoint detection or a manual stop. When the reply finishes and Gennie returns to the lamp, the wake listener is armed again.

The manual microphone button uses the same handoff: it requests interruption of the wake worker, waits for its `finished` signal, and only then starts streaming ASR.

## Speech output

`SpeechOutputWorker` calls macOS `say` outside the Qt UI thread. It prefers Ava when installed, then Samantha and other English voices, and supports `GENNIE_TTS_VOICE` and `GENNIE_TTS_RATE`. No remote speech service is included.

## AI and memory

`ChatWorker` keeps local Ollama inference off the GUI thread. `GennieBrain` retrieves context from PostgreSQL and saves conversation turns using the existing schema. The assistant output is filtered to remove emoji, and the system prompt strongly prioritizes concise replies.

Persistent database table names remain `tuna_*` to preserve existing user data. The application identity is Project Gennie.

## Model storage

Wake-word and streaming-ASR model weights live in `models/`, which is excluded from Git. `scripts/setup_asr_model.sh` downloads the English streaming ASR model locally. `scripts/configure_gennie_wakeword.sh` creates Gennie's BPE keyword aliases from the locally installed wake-word model.
