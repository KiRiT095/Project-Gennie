# Tuna AI integration v0.4

## What this segment adds

- A replaceable chat-provider contract and an Ollama implementation.
- Tuna's personality in `app/brain/prompts/system_prompt.txt`, independent of the model.
- Bounded in-session context and restoration of the latest conversation from PostgreSQL.
- PostgreSQL tables for conversations, messages and selective long-term memories.
- Conservative LLM-assisted memory extraction for messages likely to contain durable facts.
- Explicit `/remember`, `/memories` and `/forget` controls.
- A Qt worker thread for model inference, keeping the desktop event loop responsive.

## Current scope and honest limitations

This is the first local AI segment, not the complete multi-device system. The app does not yet synchronise memory to other devices. It uses PostgreSQL full-text search for memory retrieval; semantic embeddings/pgvector are a later enhancement. The memory extractor only analyses messages that pass a conservative phrase-based candidate filter, and runs after the reply in a background worker. A memory extraction can therefore finish shortly after the visible response.

If PostgreSQL is unavailable, Tuna can still chat and retain context in the running session, but persistent conversation history and long-term memory are offline. The app displays the database connection status in the conversation history.

## Requirements

- Python 3.11 or newer.
- Ollama running locally, with the selected model already downloaded. The default is `qwen3:4b`.
- PostgreSQL running locally, with a database named `tuna`.

## Install Python dependencies

From the project root with the virtual environment activated:

```bash
python -m pip install -e .
```

This installs PySide6 and Psycopg 3.3 or newer with its binary extra. The current Psycopg documentation lists support for Python 3.10–3.15 and PostgreSQL 10–18.

## Configure Ollama

Defaults:

- `TUNA_OLLAMA_URL=http://127.0.0.1:11434`
- `TUNA_MODEL=qwen3:4b`

The provider uses Ollama's native `/api/chat` endpoint, sends `think: false`, and displays only `message.content`, not the separate thinking field. If the model isn't downloaded, run `ollama pull qwen3:4b`.

Optional overrides can be exported in the shell before launching Tuna:

```bash
export TUNA_OLLAMA_URL="http://127.0.0.1:11434"
export TUNA_MODEL="qwen3:4b"
```

## Configure PostgreSQL on macOS

The default connection string is `postgresql:///tuna`, which uses the local PostgreSQL socket and the current macOS account as the database role. After confirming PostgreSQL is installed and running, create the database once:

```bash
createdb tuna
```

Then launch Tuna. On first successful connection, it creates its own `tuna_conversations`, `tuna_messages` and `tuna_memories` tables. It does not alter other databases such as Career-OS.

If your local PostgreSQL setup uses a password or a different host/port, set a connection URL instead:

```bash
export TUNA_DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/tuna"
```

Do not commit credentials or put passwords in source files.

## Memory commands

- `/remember <fact>` — explicitly save a fact as long-term memory.
- `/memories` — list saved memories. Tuna can also answer natural questions such as `What do you remember about me?`.
- `/forget <phrase>` — delete memories whose content/key contains the phrase.
- `/status` — show the selected model and memory database status.
- `/help` — show available commands.

Natural statements such as `My name is ...`, `I prefer ...`, `I'm building ...`, or `I decided ...` are considered extraction candidates. A few explicit patterns are stored directly with high confidence; other candidates are checked by a separate model call in the background. Low-confidence items and obvious secrets are rejected. This is a useful first filter, not a guarantee of perfect classification. Always inspect memories with `/memories`.

`/clear` starts a fresh conversation context while retaining older conversation history and long-term memories in PostgreSQL. Use `/forget` for a memory, and use database backup/administration tools for full conversation-history deletion in this initial release. You can also say `Forget <phrase>` in natural language.

## Run and test

```bash
python -m unittest discover -s tests -v
python main.py
```

The tests use fake providers/stores for AI and memory logic. They do not require Ollama or a live PostgreSQL server. Live integration still needs to be tested on the Mac after PostgreSQL is configured.
