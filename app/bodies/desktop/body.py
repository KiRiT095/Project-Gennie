"""Desktop-specific application composition and lifecycle."""

import sys

from PySide6.QtWidgets import QApplication

from app.bodies.desktop.window import MainWindow
from app.core.lifecycle import Lifecycle
from app.core.state_machine import StateMachine


class DesktopBody:
    def __init__(self) -> None:
        self.application = QApplication(sys.argv)
        self.application.setApplicationName("Tuna")
        self.application.setQuitOnLastWindowClosed(True)
        self.state_machine = StateMachine()
        self.lifecycle = Lifecycle(self.state_machine)
        self.window = MainWindow(self.state_machine)

    def run(self) -> int:
        self.lifecycle.start()
        self.window.refresh_state()
        self.window.show()
        return self.application.exec()
