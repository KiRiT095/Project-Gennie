"""Qt worker that keeps model inference off the UI thread."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.brain.brain import TunaBrain
from app.memory.manager import MemoryManager


class ChatWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, brain: TunaBrain, memory: MemoryManager, message: str) -> None:
        super().__init__()
        self.brain = brain
        self.memory = memory
        self.message = message

    def run(self) -> None:
        try:
            reply = self.brain.respond(self.message)
            self.succeeded.emit(reply)
            self.memory.schedule_extraction(self.message)
        except Exception as exc:
            self.failed.emit(str(exc))
