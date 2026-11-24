# Tuna

**A persistent, local-first AI companion.**

Tuna is an experimental desktop AI companion designed to feel less like a disposable chatbot and more like a consistent digital presence. The long-term goal is for Tuna to keep the same identity across devices while each device runs its own local AI runtime.

> **Current release:** `v1.0.0-beta.1`  
> **Status:** Early beta — active development

## What Tuna is

Tuna is built around three ideas:

- **Persistent identity:** Tuna's personality and interaction style should remain consistent across models and devices.
- **Local-first operation:** The desktop build uses a locally running language model and a local PostgreSQL database.
- **A character-first interface:** Tuna has a compact animated desktop presence, with a larger conversation view when needed.

Tuna is a personal project and an evolving experiment. Features described as planned or experimental are not guaranteed to be production-ready.

## Current features

### Desktop companion

- PySide6 desktop application.
- Compact floating window with an animated pixel-art fish avatar.
- Expanded conversation view.
- Avatar expressions and animation states, including idle, listening, thinking, speaking, sleeping, confused and happy.
- Conversation input and visible response history.

### Local AI

- Ollama provider integration.
- Configurable local model.
- Current tested model: `qwen3:4b-instruct-2507-q4_K_M`.
- System personality prompt stored separately from application logic.
- Background chat worker so model requests do not block the UI.

### Persistent data and memory

- PostgreSQL-backed conversations, messages and memories.
- Conversation restoration from the database.
- Memory extraction and retrieval components.
- Local database credentials configured through environment variables.

### Voice — experimental

The first voice-recognition work is underway:

- `sherpa-onnx` speaker embedding model installed and loaded successfully.
- The selected Titanet model returns 192-dimensional speaker embeddings.
- `sounddevice` microphone capture tested at 16 kHz on the MacBook Air microphone.
- Voice enrollment and speaker verification are the next development steps.

**Important:** Voice speaker recognition is probabilistic. It is not secure authentication and must not be used as the sole protection for sensitive actions.

## Architecture at a glance

```text
PySide6 desktop interface
        |
        +---- Animated avatar and UI state
        |
        +---- Chat worker
                  |
                  v
              TunaBrain
                  |
                  v
             Ollama provider
                  |
                  v
             Local Ollama model

TunaBrain / memory components
        |
        v
  PostgreSQL database

Experimental voice pipeline
        |
        +---- Microphone capture
        +---- Speaker embeddings
        +---- Speaker verification (in progress)
        +---- Speech recognition (planned)
        +---- Text-to-speech (planned)
```

Each device is intended to run its own local AI runtime and personality configuration. The long-term cross-device design shares **memory**, not the model runtime or local tools. Secure memory synchronisation is a future feature, not part of this beta.

## Requirements

The current development setup is:

- macOS on Apple Silicon (tested on an M1 MacBook Air with 8 GB RAM).
- Python 3.14.
- Ollama.
- PostgreSQL 18.
- A local Ollama model.
- Microphone access for experimental voice work.

Other operating systems and hardware have not been validated.

## Development setup

The commands below are a starting point for the current macOS development setup. Check the repository's `pyproject.toml` and `requirements.txt` for the authoritative dependency list.

```bash
git clone https://github.com/KiRiT095/Project-Tuna.git
cd Project-Tuna

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the project uses editable installation through `pyproject.toml`, install it with:

```bash
pip install -e .
```

### Configure environment

Create a local `.env` file in the project root. Do not commit it.

Example structure (use your own database credentials):

```dotenv
TUNA_MODEL=qwen3:4b-instruct-2507-q4_K_M
TUNA_OLLAMA_URL=http://127.0.0.1:11434
TUNA_DATABASE_URL=postgresql://tuna_user:YOUR_PASSWORD@localhost:5432/tuna
```

Ensure Ollama is running and the configured model is available locally:

```bash
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama list
```

Create the PostgreSQL role and database according to your local PostgreSQL setup. The application expects the database connection string to be supplied through the environment.

Start Tuna using the project's entry point:

```bash
python main.py
```

If your local checkout uses a different entry point or configuration, follow the current source code and project instructions.

## Voice development notes

The experimental speaker-recognition model is expected at:

```text
models/speaker/nemo_en_titanet_small.onnx
```

The model is not necessarily included in the Git repository. Follow the project's model download instructions and check the model's licence and redistribution terms before distributing it.

Voice profile data should remain outside the repository, under the user's local application-support directory. Do not commit voice recordings, embeddings, or personal voice profiles.

## Security and privacy

- Keep `.env` and all credentials out of version control.
- Do not expose the PostgreSQL server directly to the public internet.
- Do not commit database dumps, conversation databases, voice recordings or speaker profiles.
- Treat speaker recognition as a convenience feature, not an authentication boundary.
- Review model and dependency licences before redistributing binaries or models.

## Known limitations

- This is an early beta, not a production-ready application.
- The currently validated environment is a specific Apple Silicon macOS setup.
- Voice enrollment and reliable speaker verification are still being developed.
- Speech-to-text, text-to-speech and wake-word support are not yet established as complete features.
- Cross-device memory synchronisation is planned, not implemented.
- The macOS app wrapper is not currently part of the validated setup.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the planned development direction and [CHANGELOG.md](CHANGELOG.md) for release history.

## Contributing

Tuna is evolving quickly. If you want to experiment with the project:

1. Open an issue describing the problem or proposed change.
2. Keep changes focused and avoid committing personal data or local configuration.
3. Run the available tests before submitting a change.
4. Document new environment variables, dependencies and setup steps.

## Licence

No licence is declared here. Until a licence is added to the repository, assume that the project is not licensed for redistribution or reuse beyond what applicable law permits.
