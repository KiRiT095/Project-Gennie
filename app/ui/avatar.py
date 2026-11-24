"""Pixel-art avatar widget with state-driven expressions."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class AvatarWidget(QLabel):
    """Displays Tuna's expression without coupling the UI to core logic."""

    EXPRESSION_BY_STATE = {
        "BOOTING": "happy",
        "IDLE": "idle",
        "LISTENING": "listening",
        "THINKING": "thinking",
        "SPEAKING": "speaking",
        "SLEEPING": "sleeping",
        "ERROR": "confused",
    }

    def __init__(self, size: int = 150, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("avatar")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(size, size)
        self.setScaledContents(False)

        project_root = Path(__file__).resolve().parents[2]
        self.asset_dir = project_root / "assets" / "expressions"
        self._pixmaps = {
            name: QPixmap(str(self.asset_dir / f"{name}.png"))
            for name in self.EXPRESSION_BY_STATE.values()
        }
        self._expression = "idle"
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(4200)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_timer.start()
        self._set_pixmap()

    def set_state(self, state: str) -> None:
        expression = self.EXPRESSION_BY_STATE.get(state, "confused")
        self.set_expression(expression)

    def set_expression(self, expression: str) -> None:
        if expression not in self._pixmaps:
            expression = "confused"
        self._expression = expression
        self._set_pixmap()

    def _set_pixmap(self) -> None:
        pixmap = self._pixmaps.get(self._expression)
        if pixmap is None or pixmap.isNull():
            self.setText("( o   o )")
            return
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.setPixmap(scaled)

    def _blink(self) -> None:
        if self._expression != "idle":
            return
        self.set_expression("blink")
        QTimer.singleShot(180, self._restore_idle)

    def _restore_idle(self) -> None:
        if self._expression == "blink":
            self.set_expression("idle")
