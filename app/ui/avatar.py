"""Animated pixel-art avatar for Tuna's desktop body."""

from __future__ import annotations

import math
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class AvatarWidget(QWidget):
    """Draws Tuna's expression and adds subtle state-aware motion.

    Core state names are translated into visual expressions here. The state
    machine itself stays independent of Qt and image assets.
    """

    EXPRESSION_BY_STATE = {
        "BOOTING": "happy",
        "IDLE": "idle",
        "LISTENING": "listening",
        "THINKING": "thinking",
        "SPEAKING": "speaking",
        "SLEEPING": "sleeping",
        "ERROR": "confused",
    }

    def __init__(self, size: int = 176, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("avatar")
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        project_root = Path(__file__).resolve().parents[2]
        self.asset_dir = project_root / "assets" / "expressions"
        self._pixmaps = {
            name: QPixmap(str(self.asset_dir / f"{name}.png"))
            for name in set(self.EXPRESSION_BY_STATE.values()) | {"blink"}
        }

        self._state = "IDLE"
        self._expression = "idle"
        self._started_at = time.monotonic()
        self._next_blink_at = self._started_at + 4.8
        self._blink_until = 0.0

        # A lightweight timer drives drawing only; it does not run background
        # work or block the Qt event loop.
        self._motion_timer = QTimer(self)
        self._motion_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._motion_timer.setInterval(33)  # approximately 30 visual frames/sec
        self._motion_timer.timeout.connect(self._animate)
        self._motion_timer.start()

    @property
    def current_state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        """Update the avatar only when Tuna's behavioural state changes."""
        expression = self.EXPRESSION_BY_STATE.get(state, "confused")
        if state == self._state and expression == self._expression:
            return

        self._state = state
        self._expression = expression
        now = time.monotonic()
        self._blink_until = 0.0
        self._next_blink_at = now + 4.8
        self.update()

    def set_expression(self, expression: str) -> None:
        """Set a visual expression directly (useful for future emotion events)."""
        if expression not in self._pixmaps:
            expression = "confused"
        self._expression = expression
        self.update()

    def _animate(self) -> None:
        now = time.monotonic()
        if self._state == "IDLE":
            if self._blink_until and now >= self._blink_until:
                self._blink_until = 0.0
            if not self._blink_until and now >= self._next_blink_at:
                self._blink_until = now + 0.15
                self._next_blink_at = now + 4.8
        self.update()

    def _pose(self, elapsed: float) -> tuple[float, float, float]:
        """Return vertical offset, scale and rotation for the active state."""
        if self._state == "IDLE":
            return 3.0 * math.sin(elapsed * 2.0), 1.0 + 0.012 * math.sin(elapsed * 1.5), 0.0
        if self._state == "LISTENING":
            return 1.2 * math.sin(elapsed * 2.8), 1.0 + 0.014 * math.sin(elapsed * 2.0), 0.0
        if self._state == "THINKING":
            return 1.5 * math.sin(elapsed * 1.7), 1.0, 2.0 * math.sin(elapsed * 1.35)
        if self._state == "SPEAKING":
            return 1.0 * math.sin(elapsed * 14.0), 1.0 + 0.012 * math.sin(elapsed * 14.0), 0.0
        if self._state == "SLEEPING":
            return 1.4 * math.sin(elapsed * 0.8), 1.0, 0.0
        if self._state == "ERROR":
            return 0.0, 1.0, 1.2 * math.sin(elapsed * 2.6)
        # A little buoyancy for the brief BOOTING/HAPPY pose.
        return 2.0 * math.sin(elapsed * 2.4), 1.0 + 0.014 * math.sin(elapsed * 2.4), 0.0

    def _active_pixmap(self, elapsed: float) -> QPixmap:
        if self._state == "IDLE" and time.monotonic() < self._blink_until:
            return self._pixmaps.get("blink", QPixmap())

        # Alternate between the closed smile and open-mouth sprite while
        # speaking. This creates a simple two-frame talking animation.
        if self._state == "SPEAKING":
            frame = "speaking" if int(elapsed / 0.19) % 2 == 0 else "idle"
            return self._pixmaps.get(frame, QPixmap())

        return self._pixmaps.get(self._expression, QPixmap())

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override name
        elapsed = time.monotonic() - self._started_at
        vertical_offset, scale, rotation = self._pose(elapsed)
        pixmap = self._active_pixmap(elapsed)
        if pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.translate(self.width() / 2.0, self.height() / 2.0 + vertical_offset)
        painter.rotate(rotation)
        painter.scale(scale, scale)

        draw_size = min(self.width(), self.height()) * 0.94
        target = QRectF(-draw_size / 2.0, -draw_size / 2.0, draw_size, draw_size)
        source = QRectF(pixmap.rect())
        painter.drawPixmap(target, pixmap, source)
        painter.end()
