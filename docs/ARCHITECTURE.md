# Architecture

## Current desktop shape

```text
main.py
  └── DesktopBody
       ├── QApplication / Qt event loop
       ├── Lifecycle
       │    └── StateMachine
       └── MainWindow
            ├── AvatarWidget
            │    └── expression PNG assets + timer-driven motion
            ├── temporary transcript/caption labels
            └── expanded-only history and text input
```

`StateMachine` is framework-independent. It validates behavioural state transitions. `Lifecycle` coordinates startup. `DesktopBody` composes the desktop application. `MainWindow` decides what is visible and collects text input. `AvatarWidget` translates the current state into a visual expression and subtle motion.

## Compact and expanded presentation

Compact mode contains only Tuna's character, except when a temporary speech transcript or assistant subtitle has content. There is no permanent state label or instruction prompt. Clicking the character opens the conversation view. Expanded mode shows the header, conversation history, text input, and the same character at the top. Escape or the Compact control returns to compact mode.

## Animation approach

The avatar uses the expression PNGs as sprite frames. A small Qt timer triggers repainting at about 30 frames per second. The paint method computes a subtle pose from elapsed time: idle floating, listening pulse, thinking tilt, and a speaking open/closed-mouth cycle. Idle blinking temporarily displays the blink sprite. This is code-driven animation; there is no video or animated GIF playback.

## Boundaries

- Core must not import PySide6.
- UI must not own a duplicate state value.
- The state label is intentionally not shown; the avatar expresses state.
- Speech/transcription methods are display hooks, not audio capture or speech recognition.
- Wake-word listening must be opt-in and should include microphone permission, visible listening state, mute/disable controls, and local processing.
- Future command execution must use explicit allowlisted capabilities and permission checks, never arbitrary model-generated shell commands.
