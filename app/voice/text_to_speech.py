"""Warm, local macOS speech output using the system speech voices."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import time

from PySide6.QtCore import QThread, Signal


VOICE_PREFERENCES = ("Ava", "Samantha", "Allison", "Victoria", "Zoe", "Susan")


def list_macos_voices() -> list[tuple[str, str]]:
    """Return installed (voice name, locale) pairs reported by macOS `say`."""
    if platform.system() != "Darwin":
        return []
    result = subprocess.run(
        ["say", "-v", "?"], capture_output=True, text=True, check=False, timeout=8
    )
    voices: list[tuple[str, str]] = []
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        match = re.match(r"^(.+?)\s+([a-z]{2}_[A-Z]{2})\s+#", line.strip())
        if match:
            voices.append((match.group(1).strip(), match.group(2)))
    return voices


def choose_voice(requested: str = "") -> str:
    """Prefer a soft female English voice; fall back to an installed English voice."""
    voices = list_macos_voices()
    if not voices:
        return ""
    requested = requested.strip() or os.getenv("GENNIE_TTS_VOICE", "").strip()
    if requested:
        match = next(
            (name for name, _ in voices if name.casefold() == requested.casefold()
             or name.casefold().startswith(requested.casefold() + " ")),
            None,
        )
        if match:
            return match
    english = [(name, locale) for name, locale in voices if locale.casefold().startswith("en_")]
    candidates = english or voices
    for preferred in VOICE_PREFERENCES:
        match = next(
            (name for name, _ in candidates if name.casefold() == preferred.casefold()
             or name.casefold().startswith(preferred.casefold() + " ")),
            None,
        )
        if match:
            return match
    return candidates[0][0]


def speech_text(text: str) -> str:
    """Remove markdown markers and emoji from the spoken rendering."""
    cleaned = re.sub(r"```.*?```", "Code block omitted.", text, flags=re.DOTALL)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+[.)]\s+", "", cleaned)
    cleaned = re.sub(r"[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


class SpeechOutputWorker(QThread):
    failed = Signal(str)
    voice_selected = Signal(str)

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.text = speech_text(text)
        self._process: subprocess.Popen | None = None
        try:
            self.rate = max(130, min(230, int(os.getenv("GENNIE_TTS_RATE", "174"))))
        except ValueError:
            self.rate = 178
        self.requested_voice = os.getenv("GENNIE_TTS_VOICE", "").strip()

    def stop(self) -> None:
        self.requestInterruption()
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    def run(self) -> None:
        if not self.text:
            return
        if platform.system() != "Darwin":
            self.failed.emit("Speech output currently uses the built-in macOS voices.")
            return
        try:
            voice = choose_voice(self.requested_voice)
            self.voice_selected.emit(voice or "System default")
            command = ["say", "-r", str(self.rate)]
            if voice:
                command.extend(["-v", voice])
            command.append(self.text)
            self._process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            while self._process.poll() is None:
                if self.isInterruptionRequested():
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                    return
                time.sleep(0.08)
            if self._process.returncode:
                error = (self._process.stderr.read() if self._process.stderr else "").strip()
                raise RuntimeError(error or "The macOS speech service returned an error.")
        except Exception as exc:
            self.failed.emit(f"Speech output failed: {exc}")
        finally:
            self._process = None
