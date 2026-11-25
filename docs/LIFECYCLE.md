# Gennie lifecycle

| State | Visual | Purpose |
|---|---|---|
| `BOOTING` | brief launch | Initialise app |
| `SLEEPING` | lamp | Resting in lamp; wake listener armed |
| `EMERGING` | lamp glow, smoke, genie rise | Wake/manual summon animation |
| `LISTENING` | genie | Input is being received by the UI |
| `THINKING` | thoughtful genie frames | Local model is working |
| `SPEAKING` | gesture/talk frames | Assistant response is displayed |
| `RETURNING` | genie sinks into smoke/lamp | Inactivity/sleep animation |
| `IDLE` | genie | Brief active idle after a turn |
| `ERROR` | fallback | Recoverable error |

The lamp state is not microphone-off: the local wake-word worker remains active while the application is open. Quit the application to stop microphone capture.
