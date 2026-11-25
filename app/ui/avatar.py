"""Pixel-art Gennie avatar with a tiny, curious dormant companion mode."""

from __future__ import annotations

import math
import random
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget


class AvatarWidget(QWidget):
    """A small wandering genie while dormant; full-size Gennie when summoned."""

    FRAME_SEQUENCES = {
        "IDLE": (0, 0, 0, 0, 1, 0, 0, 2),
        "LISTENING": (4, 4, 5, 4, 6, 4),
        "THINKING": (7, 7, 9, 7, 9, 7),
        "SPEAKING": (5, 6, 10, 11, 10, 6),
    }

    def __init__(self, size: int = 238, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("gennieAvatar")
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        root = Path(__file__).resolve().parents[2]
        self.asset_dir = root / "assets" / "gennie"
        self.frames = [QPixmap(str(self.asset_dir / "frames" / f"frame_{i:02d}.png")) for i in range(16)]
        self.dormant_frames = [QPixmap(str(self.asset_dir / "dormant" / f"dormant_{i:02d}.png")) for i in range(12)]
        self.lamp = QPixmap(str(self.asset_dir / "lamp_idle.png"))
        self.lamp_glow = QPixmap(str(self.asset_dir / "lamp_glow.png"))
        self._state = "SLEEPING"
        self._started = time.monotonic()
        self._expression_frame: int | None = None
        self._dormant_frame = 0
        self._next_dormant_change = self._started + 2.6
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    @property
    def current_state(self) -> str:
        return self._state

    def set_avatar_size(self, size: int) -> None:
        self.setFixedSize(size, size)
        self.update()

    def set_state(self, state: str) -> None:
        if state == self._state:
            return
        self._state = state
        self._started = time.monotonic()
        self._expression_frame = None
        if state in {"BOOTING", "SLEEPING"}:
            self._dormant_frame = 0
            self._next_dormant_change = self._started + 2.6
        self.update()

    def set_expression(self, expression: str) -> None:
        mapping = {"neutral": 0, "happy": 5, "thinking": 9, "listening": 4, "laughing": 3, "explaining": 10, "confident": 15}
        self._expression_frame = mapping.get(expression, 0)
        self.update()

    def _tick(self) -> None:
        now = time.monotonic()
        if self._state in {"BOOTING", "SLEEPING"} and now >= self._next_dormant_change:
            # Hold each tiny pose long enough to feel like a creature, not a GIF.
            self._dormant_frame = random.choices(
                population=(3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2),
                weights=(14, 12, 10, 10, 10, 10, 8, 8, 8, 5, 5),
                k=1,
            )[0]
            self._next_dormant_change = now + random.uniform(2.2, 5.8)
        self.update()

    def _draw_lamp(self, painter: QPainter, glow: bool = False) -> None:
        pixmap = self.lamp_glow if glow else self.lamp
        if pixmap.isNull():
            return
        pulse = 0.82 + 0.15 * math.sin((time.monotonic() - self._started) * 2.2) if glow else 1.0
        painter.setOpacity(pulse)
        w = self.width() * 0.82
        h = w * pixmap.height() / max(1, pixmap.width())
        target = QRectF((self.width()-w)/2, self.height()-h-10, w, h)
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        painter.setOpacity(1.0)

    def _draw_smoke(self, painter: QPainter, progress: float) -> None:
        t = time.monotonic() - self._started
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(7):
            phase = t * 2.4 + index * 0.86
            x = self.width()/2 + math.sin(phase) * (18 + index*2)
            y = self.height() * 0.70 - progress * 66 - index * 8 + math.cos(phase) * 4
            size = 4 + (index % 3) * 2
            alpha = max(0, int(150 * progress * (1 - index/10)))
            painter.setBrush(QColor(154, 100, 255, alpha))
            painter.drawRect(int(x), int(y), size, size)
            painter.setBrush(QColor(75, 174, 255, alpha//2))
            painter.drawRect(int(x+4), int(y+3), max(2,size//2), max(2,size//2))

    def _draw_genie(self, painter: QPainter, frame_index: int, y_offset: float = 0.0, opacity: float = 1.0, scale: float = 1.0) -> None:
        if not self.frames:
            return
        pixmap = self.frames[frame_index % len(self.frames)]
        if pixmap.isNull():
            return
        max_w = self.width() * 1.04 * scale
        max_h = self.height() * 1.04 * scale
        ratio = min(max_w / pixmap.width(), max_h / pixmap.height())
        w, h = pixmap.width()*ratio, pixmap.height()*ratio
        target = QRectF((self.width()-w)/2, (self.height()-h)/2 + y_offset, w, h)
        painter.setOpacity(max(0.0, min(1.0, opacity)))
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        painter.setOpacity(1.0)

    def _draw_dormant_sprite(self, painter: QPainter, elapsed: float) -> None:
        if not self.dormant_frames:
            self._draw_lamp(painter, glow=True)
            return
        # The first three frames show her sneaking out. Once free, she uses
        # small, distinct curious/hovering poses with long natural pauses.
        if elapsed < 2.6:
            frame = min(2, int(elapsed / 0.87))
        else:
            frame = self._dormant_frame
        pixmap = self.dormant_frames[frame]
        if pixmap.isNull():
            return
        bob = math.sin(elapsed * 1.25) * 1.8
        target_w = self.width() * 0.76
        target_h = target_w * pixmap.height() / max(1, pixmap.width())
        target = QRectF((self.width()-target_w)/2, (self.height()-target_h)/2 + bob, target_w, target_h)
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        elapsed = time.monotonic() - self._started

        if self._state in {"BOOTING", "SLEEPING"}:
            self._draw_dormant_sprite(painter, elapsed)
            painter.end()
            return

        if self._state == "EMERGING":
            progress = min(1.0, elapsed / 1.25)
            self._draw_lamp(painter, glow=True)
            self._draw_smoke(painter, progress)
            emergence_frames = (12, 13, 14, 15)
            frame = emergence_frames[min(len(emergence_frames) - 1, int(progress * len(emergence_frames)))]
            self._draw_genie(painter, frame, y_offset=54*(1-progress), opacity=progress, scale=0.82+0.18*progress)
            painter.end()
            return

        if self._state == "RETURNING":
            progress = min(1.0, elapsed / 1.15)
            self._draw_lamp(painter, glow=True)
            self._draw_smoke(painter, 1.0-progress)
            return_frames = (15, 14, 13, 12)
            frame = return_frames[min(len(return_frames) - 1, int(progress * len(return_frames)))]
            self._draw_genie(painter, frame, y_offset=progress*64, opacity=1.0-progress, scale=1.0-0.18*progress)
            painter.end()
            return

        sequence = self.FRAME_SEQUENCES.get(self._state, (0,))
        frame = self._expression_frame if self._expression_frame is not None else sequence[int(elapsed * (3.2 if self._state == "IDLE" else 5.5)) % len(sequence)]
        bob = math.sin(elapsed * 1.8) * 2.8 if self._state in {"IDLE", "LISTENING"} else math.sin(elapsed * 6.0) * 1.6
        self._draw_genie(painter, frame, y_offset=bob)
        painter.end()
