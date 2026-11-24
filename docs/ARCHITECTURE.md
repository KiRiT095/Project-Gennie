# Tuna architecture

## Current desktop composition

```text
main.py
  └── DesktopBody
       ├── QApplication / Qt event loop
       ├── Lifecycle
       │    └── StateMachine
       └── MainWindow
            ├── AvatarWidget (state -> expression)
            ├── subtitle/transcription displays
            └── expanded conversation history + text input
```

## Boundaries

- `app/core` is framework-independent and owns state/lifecycle rules.
- `app/ui` contains reusable presentation components, including the avatar.
- `app/bodies/desktop` owns the Qt desktop application and window behaviour.
- The UI reads the shared StateMachine; it does not maintain a second state value.
- A future `voice` package should provide speech-to-text, text-to-speech and wake-word services behind separate interfaces. The UI should receive events/transcripts and must not own microphone capture internals.
- A future `brain` provider should be replaceable and must not be allowed arbitrary shell execution. Device capabilities must be explicitly allowlisted and permission-controlled.

## Window modes

- **Compact:** character, state, and temporary caption/transcription only. No chat input or history is visible.
- **Expanded:** avatar and state remain at the top; conversation history and text input appear below.

Clicking the compact window expands it. `Compact` or Escape returns to compact mode. The window is frameless and stays above normal windows; in expanded mode its top header can be dragged. Right-click opens a small context menu.

## Voice UI hooks

`MainWindow.show_user_transcription(text)` displays a user's recognised speech. `MainWindow.show_assistant_subtitle(text)` displays an assistant subtitle. These are presentation hooks only; neither performs audio capture, transcription or speech synthesis.
