"""Desktop composition and lifecycle for Project Gennie."""

import os
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.brain.brain import GennieBrain
from app.brain.conversation import Conversation
from app.brain.providers.ollama import OllamaProvider
from app.bodies.desktop.window import MainWindow
from app.core.lifecycle import Lifecycle
from app.core.state_machine import StateMachine
from app.database.postgres import PostgresStore
from app.memory.manager import MemoryManager
from app.voice.wake_word import WakeWordWorker


class DesktopBody:
    def __init__(self) -> None:
        load_dotenv()
        self.application = QApplication(sys.argv)
        self.application.setApplicationName("Project Gennie")
        icon_path = Path(__file__).resolve().parents[3] / "assets" / "gennie" / "gennie_icon.png"
        self.application.setWindowIcon(QIcon(str(icon_path)))
        self.application.setQuitOnLastWindowClosed(True)

        self.state_machine = StateMachine()
        self.lifecycle = Lifecycle(self.state_machine)

        # Keep the existing tables and stored conversations/memories unchanged.
        self.store = PostgresStore()
        database_ready = self.store.initialize()
        conversation_id, previous_messages = self.store.latest_or_create_conversation(str(uuid4()))
        self.conversation = Conversation(conversation_id, previous_messages)

        self.provider = OllamaProvider()
        self.memory = MemoryManager(self.store, self.provider)
        self.brain = GennieBrain(self.provider, self.conversation, self.store)
        self.wake_worker = WakeWordWorker()
        memory_status = (
            "PostgreSQL memory is connected. Your saved memories and recent conversation can persist."
            if database_ready and self.store.available
            else f"PostgreSQL memory is offline: {self.store.last_error} Gennie can still chat, but long-term memory is not being saved yet."
        )
        self.window = MainWindow(
            self.state_machine, self.brain, self.memory,
            memory_status=memory_status, wake_worker=self.wake_worker,
        )
        self.application.aboutToQuit.connect(self.shutdown)

    def run(self) -> int:
        self.lifecycle.start()
        # Startup settles into the lamp; the local wake-word thread stays armed.
        self.state_machine.change_state("SLEEPING")
        self.window.refresh_state()
        self.window.show()
        self.window.start_dormant_flight()
        wake_enabled = os.getenv("GENNIE_WAKE_ENABLED", "true").strip().casefold() not in {"0", "false", "no", "off"}
        if wake_enabled:
            self.wake_worker.start()
        else:
            self.window._on_wake_status("Wake-word listener is disabled by GENNIE_WAKE_ENABLED.")
        return self.application.exec()

    def shutdown(self) -> None:
        # Stop all microphone/speech workers before Qt destroys the window.
        voice_worker = getattr(self.window, "_voice_worker", None)
        if voice_worker is not None and voice_worker.isRunning():
            voice_worker.request_stop()
            voice_worker.wait(2500)
        speech_worker = getattr(self.window, "_speech_worker", None)
        if speech_worker is not None and speech_worker.isRunning():
            speech_worker.stop()
            speech_worker.wait(1500)
        if self.wake_worker.isRunning():
            self.wake_worker.requestInterruption()
            self.wake_worker.wait(2500)
        self.memory.shutdown()
