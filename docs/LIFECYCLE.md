# Lifecycle

- `BOOTING`: startup coordination is in progress.
- `IDLE`: ready and waiting.
- `LISTENING`: receiving/attending to user input.
- `THINKING`: processing a request.
- `SPEAKING`: presenting a response (text in this prototype; audio later).
- `SLEEPING`: deliberately reduced activity until wake.
- `ERROR`: a fault is exposed; a separate handler will eventually diagnose/recover.

The state machine validates state transitions. It does not perform the work associated with each state. The Qt event loop is separate and must not be blocked by long-running work.
