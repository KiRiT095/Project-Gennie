# Code review and fixes in 1.1.0

- Replaced the old purple card-heavy interface with a small black window and a two-dot face.
- The old pytest run attempted to import `scripts/test_wakeword.py` as a test module, which failed when optional microphone packages were absent. Renamed it to `wakeword_smoke_test.py` and moved optional imports inside `main()`.
- The previous keyword list used only the brand spelling `GENNIE`. The wake model is trained on ordinary English speech and may decode that pronunciation as `JENNY` or `GENIE`; setup now creates both aliases using the model's own BPE tokenizer.
- The wake listener now exits its `InputStream` immediately after detection. Recording begins only after the worker finishes, preventing two threads from trying to own the microphone at once.
- Added a local seven-second push-to-talk capture path using whisper.cpp `tiny.en`; no cloud transcription is involved.
- Added macOS `say` output so responses can be heard. The wake listener restarts after speech output.
- Added a small original synthesized retro chirp; no third-party game audio is included.
- Fixed shutdown to stop the currently active wake worker, not only the worker created at application startup.
- Kept the existing PostgreSQL table names, model configuration fallbacks and saved memory data.

## Validation boundary

`python -m compileall -q app scripts` succeeds and the automated suite reports 22 passing tests. This build environment does not have the user's macOS microphone, Ollama instance or PySide6 desktop session, so live wake-word accuracy, actual audio device selection and GUI rendering must still be checked on the Mac.
