"""Desktop-specific application composition and lifecycle."""

import sys
from uuid import uuid4
from dotenv import load_dotenv

from PySide6.QtWidgets import QApplication

from app.brain.brain import TunaBrain
from app.brain.conversation import Conversation
from app.brain.providers.ollama import OllamaProvider
from app.bodies.desktop.window import MainWindow
from app.core.lifecycle import Lifecycle
from app.core.state_machine import StateMachine
from app.database.postgres import PostgresStore
from app.memory.manager import MemoryManager


class DesktopBody:
    def __init__(self) -> None:
        load_dotenv()
        self.application = QApplication(sys.argv)
        self.application.setApplicationName("Tuna")
        self.application.setQuitOnLastWindowClosed(True)

        self.state_machine = StateMachine()
        self.lifecycle = Lifecycle(self.state_machine)

        # PostgreSQL is local-first. If it is not installed/running yet, Tuna
        # still starts and can chat; persistent memory is clearly marked offline.
        self.store = PostgresStore()
        database_ready = self.store.initialize()
        conversation_id, previous_messages = self.store.latest_or_create_conversation(
            str(uuid4())
        )
        self.conversation = Conversation(conversation_id, previous_messages)

        self.provider = OllamaProvider()
        self.memory = MemoryManager(self.store, self.provider)
        self.brain = TunaBrain(self.provider, self.conversation, self.store)
        self.window = MainWindow(
            self.state_machine,
            self.brain,
            self.memory,
            memory_status=(
                "PostgreSQL memory is connected. Your saved memories and recent conversation can persist."
                if database_ready and self.store.available
                else f"PostgreSQL memory is offline: {self.store.last_error} "
                     "Tuna can still chat, but long-term memory is not being saved yet."
            ),
        )
        self.application.aboutToQuit.connect(self.memory.shutdown)

    def run(self) -> int:
        self.lifecycle.start()
        self.window.refresh_state()
        self.window.show()
        return self.application.exec()
