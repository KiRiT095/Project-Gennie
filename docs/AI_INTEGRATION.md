# Gennie AI integration

Gennie's reasoning layer is provider-independent. The default provider connects to the local Ollama API. `GennieBrain` composes the system identity, conversation context and retrieved memories. `TunaBrain` remains as an import alias for backwards compatibility.

## Configuration

Preferred variables are `GENNIE_MODEL`, `GENNIE_OLLAMA_URL` and `GENNIE_DATABASE_URL`. Existing `TUNA_MODEL`, `TUNA_OLLAMA_URL` and `TUNA_DATABASE_URL` values remain supported as fallbacks.

The default Ollama endpoint is `http://127.0.0.1:11434`. The default model is `qwen3:4b-instruct-2507-q4_K_M`.

## PostgreSQL compatibility

The existing database and tables (`tuna_conversations`, `tuna_messages`, `tuna_memories`) are retained intentionally. The Gennie application does not rename, drop or migrate those tables. This keeps existing conversation history and saved memories accessible.

## Voice boundary

The optional local wake-word worker detects “Gennie” and summons the avatar. It is not a speech recognizer and does not verify speaker identity. Audio transcription, the enrolled speaker profile and TTS must be connected as distinct pipeline stages.
