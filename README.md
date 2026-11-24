# Tuna — Companion UI Prototype v0.2

A minimal, character-first macOS desktop companion prototype built with PySide6.

## What this version includes

- Compact, always-on-top companion window with no visible text input.
- Original pixel-art Tuna mascot with state-driven expressions and an idle blink.
- Click the compact companion to open the expanded conversation view.
- Expanded view keeps Tuna's avatar and state visible above conversation history.
- Text input is visible only in expanded mode.
- Assistant subtitle and user-transcription display hooks, with temporary captions.
- Drag the expanded window by its top header; right-click for compact/quit actions.
- Existing finite state machine and unit tests.

## What is not connected yet

This prototype is **not voice-enabled yet**. It does not currently access the microphone, transcribe speech, speak responses, or listen for a wake word in the background. The UI includes `show_user_transcription()` and `show_assistant_subtitle()` hooks for later local speech-to-text and text-to-speech services. Wake-word listening should be added only after explicit microphone permission, a visible listening indicator, mute/disable controls, and a local processing choice are in place.

The replies are placeholders; there is no LLM connected.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Launch

```bash
python main.py
```

## Interaction

- Click the compact character to expand the conversation.
- Click **Compact** or press `Esc` to return to the small companion view.
- Type `/help`, `/status`, `/sleep`, `/wake`, `/clear`, or `/demo` in expanded mode.
- Right-click for the compact/quit menu.

## Design principles

1. Tuna is character-first, not chat-first.
2. Text input is hidden during normal desktop presence.
3. Speech transcripts and assistant subtitles are separate temporary display elements.
4. Expanded history retains the avatar and current expression.
5. Voice and wake-word services remain separate from the UI and core state machine.
6. No always-on microphone access without explicit user consent and clear controls.
7. Keep the AI provider replaceable and do not grant an LLM unrestricted shell access.

See `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and `docs/VOICE_DESIGN.md`.
