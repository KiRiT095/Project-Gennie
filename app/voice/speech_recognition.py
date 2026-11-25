"""Local utterance capture and Whisper.cpp transcription for Project Gennie.

The microphone is held only while one utterance is being captured. Whisper runs
locally after capture, so the wake-word worker can safely reclaim the device.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import wave
from collections import deque
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.voice.audio_devices import select_input_device


class SpeechRecognitionWorker(QThread):
    partial_text = Signal(str)
    final_text = Signal(str)
    status = Signal(str)
    failed = Signal(str)

    SAMPLE_RATE = 16_000
    BLOCK_SIZE = 480  # 30 ms frames for voice activity detection.

    def __init__(self, project_root: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        default_model = self.project_root / "models" / "stt" / "ggml-small.en-q5_1.bin"
        configured = Path(os.getenv("GENNIE_WHISPER_MODEL", str(default_model))).expanduser()
        self.model_path = configured if configured.is_absolute() else self.project_root / configured
        self.device = os.getenv("GENNIE_MIC_DEVICE", "").strip()
        self.cli = os.getenv("GENNIE_WHISPER_CLI", "").strip() or shutil.which("whisper-cli") or shutil.which("whisper-cpp")
        self.max_seconds = self._env_float("GENNIE_VOICE_MAX_SECONDS", 20.0, 6.0, 45.0)
        self.silence_seconds = self._env_float("GENNIE_VOICE_END_SILENCE", 1.15, 0.5, 3.0)
        self.start_timeout = self._env_float("GENNIE_VOICE_START_TIMEOUT", 12.0, 4.0, 30.0)

    @staticmethod
    def _env_float(name: str, default: float, low: float, high: float) -> float:
        try:
            return max(low, min(high, float(os.getenv(name, str(default)))))
        except ValueError:
            return default

    def request_stop(self) -> None:
        """Finish the current utterance and release the microphone."""
        self.requestInterruption()

    def _capture_utterance(self):
        import numpy as np
        import sounddevice as sd

        device = select_input_device(sd, self.device)
        pre_roll: deque = deque(maxlen=8)
        recorded = []
        calibration = []
        threshold = 0.007
        speech_started = False
        silence_frames = 0
        max_frames = int(self.max_seconds * self.SAMPLE_RATE / self.BLOCK_SIZE)
        silence_limit = max(1, int(self.silence_seconds * self.SAMPLE_RATE / self.BLOCK_SIZE))
        start_limit = max(1, int(self.start_timeout * self.SAMPLE_RATE / self.BLOCK_SIZE))
        self.status.emit("Listening — speak naturally. I'll detect when you finish.")

        with sd.InputStream(
            device=device,
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=self.BLOCK_SIZE,
        ) as microphone:
            for frame_index in range(max_frames + start_limit):
                if self.isInterruptionRequested():
                    break
                samples, overflowed = microphone.read(self.BLOCK_SIZE)
                if overflowed:
                    self.status.emit("Audio buffer hiccup — keep speaking.")
                frame = np.asarray(samples, dtype=np.float32).reshape(-1).copy()
                rms = float(np.sqrt(np.mean(frame * frame) + 1e-12))

                if not speech_started:
                    pre_roll.append(frame)
                    if len(calibration) < 12:
                        calibration.append(rms)
                        if len(calibration) == 12:
                            noise_floor = float(np.median(calibration))
                            threshold = max(0.0055, min(0.025, noise_floor * 3.0))
                        continue
                    if rms >= threshold:
                        speech_started = True
                        recorded.extend(list(pre_roll))
                        self.status.emit("Hearing you…")
                    elif frame_index >= start_limit:
                        break
                else:
                    recorded.append(frame)
                    if rms < threshold:
                        silence_frames += 1
                    else:
                        silence_frames = 0
                    if silence_frames >= silence_limit:
                        break
                    if len(recorded) >= max_frames:
                        break

        if not recorded:
            if self.isInterruptionRequested():
                return None
            raise RuntimeError("I didn't hear speech. Try speaking a little closer to the MacBook microphone.")
        audio = np.concatenate(recorded).astype(np.float32, copy=False)
        peak = float(np.max(np.abs(audio)))
        if peak < 0.012:
            raise RuntimeError("The recording was too quiet. Check the selected microphone and macOS permission.")
        # Gentle peak normalisation helps quieter speech without changing pitch.
        if peak < 0.75:
            audio = np.clip(audio * (0.75 / peak), -1.0, 1.0)
        return (audio * 32767.0).astype(np.int16)

    def run(self) -> None:
        wav_path: str | None = None
        try:
            import numpy as np  # noqa: F401 - confirms the audio dependency is available
            import sounddevice  # noqa: F401

            if not self.cli:
                raise RuntimeError("Whisper.cpp is not installed. Run: bash scripts/setup_voice.sh")
            if not self.model_path.is_file():
                raise RuntimeError(
                    f"Whisper Small model is missing: {self.model_path}. Run: bash scripts/setup_voice.sh"
                )

            audio = self._capture_utterance()
            if audio is None or self.isInterruptionRequested():
                return
            fd, wav_path = tempfile.mkstemp(prefix="gennie-voice-", suffix=".wav")
            os.close(fd)
            with wave.open(wav_path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.SAMPLE_RATE)
                wav.writeframes(audio.tobytes())

            self.status.emit("Transcribing locally…")
            result = subprocess.run(
                [self.cli, "-m", str(self.model_path), "-f", wav_path,
                 "-nt", "-np", "-l", "en", "-t", "4"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if result.returncode:
                detail = (result.stderr or result.stdout or "Whisper.cpp failed").strip()
                raise RuntimeError(detail[-900:])
            transcript = " ".join(line.strip() for line in result.stdout.splitlines() if line.strip())
            transcript = transcript.strip(" \t\r\n.-")
            if not transcript:
                raise RuntimeError("I couldn't make out the words. Try again, a little closer to the microphone.")
            self.partial_text.emit(transcript)
            self.final_text.emit(transcript)
        except Exception as exc:
            self.failed.emit(f"Speech recognition failed: {exc}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
