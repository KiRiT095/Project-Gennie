"""Rounded, iOS-inspired desktop companion window with local voice chat."""

from __future__ import annotations

import os
import platform
import re
import math
import random
import time
from uuid import uuid4

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.brain.brain import GennieBrain
from app.bodies.desktop.chat_worker import ChatWorker
from app.core.state_machine import InvalidTransitionError, StateMachine
from app.memory.manager import MemoryManager
from app.ui.avatar import AvatarWidget
from app.voice.speech_recognition import SpeechRecognitionWorker
from app.voice.text_to_speech import SpeechOutputWorker
from app.voice.wake_word import WakeWordWorker


class MainWindow(QWidget):
    COMPACT_SIZE = (112, 112)
    EXPANDED_SIZE = (560, 760)

    def __init__(
        self,
        state_machine: StateMachine,
        brain: GennieBrain,
        memory: MemoryManager,
        memory_status: str = "",
        wake_worker: WakeWordWorker | None = None,
    ) -> None:
        super().__init__()
        self.state_machine = state_machine
        self.brain = brain
        self.memory = memory
        self.wake_worker = wake_worker
        self._wake_enabled = wake_worker is not None and os.getenv("GENNIE_WAKE_ENABLED", "true").strip().casefold() not in {"0", "false", "no", "off"}
        self._tts_enabled = os.getenv("GENNIE_TTS_ENABLED", "true").strip().casefold() not in {"0", "false", "no", "off"}
        self._worker: ChatWorker | None = None
        self._voice_worker: SpeechRecognitionWorker | None = None
        self._speech_worker: SpeechOutputWorker | None = None
        self._pending_voice_capture = False
        self._voice_session_active = False
        self._voice_overlay = False
        self._emergence_complete = False
        self._final_transcript = ""
        self._voice_error = ""
        self._expanded = False
        self._drag_offset: QPoint | None = None
        self._compact_press_global: QPoint | None = None
        self._compact_was_dragged = False
        self._unshown_voice_status: str | None = None
        self._flight_started = 0.0
        self._flight_active = False
        self._flight_target: QPoint | None = None
        self._flight_pause_until = 0.0
        self._flight_timer = QTimer(self)
        self._flight_timer.setInterval(33)
        self._flight_timer.timeout.connect(self._update_dormant_flight)

        try:
            self._idle_timeout_ms = max(10_000, int(os.getenv("GENNIE_IDLE_TIMEOUT_MS", "45000")))
        except ValueError:
            self._idle_timeout_ms = 45_000

        self._summon_timer = QTimer(self)
        self._summon_timer.setSingleShot(True)
        self._summon_timer.timeout.connect(self._finish_emergence)
        self._return_timer = QTimer(self)
        self._return_timer.setSingleShot(True)
        self._return_timer.timeout.connect(self._finish_return)
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.timeout.connect(self._return_to_lamp)

        if self.wake_worker is not None:
            self._connect_wake_worker(self.wake_worker)

        self._assistant_caption_timer = QTimer(self)
        self._assistant_caption_timer.setSingleShot(True)
        self._assistant_caption_timer.timeout.connect(self._clear_assistant_caption)

        self.setWindowTitle("Project Gennie")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("windowRoot")
        self.setStyleSheet("""
            QWidget#windowRoot {
                background: rgba(17, 17, 19, 250);
                border: 1px solid rgba(255, 255, 255, 24);
                border-radius: 30px;
                color: #F5F5F7;
                font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
            }
            QLabel { color: #F5F5F7; background: transparent; }
            QLabel#wordmark {
                color: #F5F5F7;
                font-size: 12px;
                font-weight: 650;
                letter-spacing: 1.8px;
            }
            QLabel#caption {
                background: rgba(39, 31, 55, 238);
                border: 1px solid rgba(166, 130, 255, 105);
                border-radius: 16px;
                padding-top: 10px;
                padding-right: 14px;
                padding-bottom: 10px;
                padding-left: 14px;
                color: #F5F5F7;
                font-size: 13px;
            }
            QLabel#userCaption {
                background: rgba(35, 43, 55, 232);
                border: 1px solid rgba(124, 178, 255, 90);
                border-radius: 14px;
                padding-top: 8px;
                padding-right: 12px;
                padding-bottom: 8px;
                padding-left: 12px;
                color: #E4EDFF;
                font-size: 12px;
            }
            QLabel#voiceStatus {
                color: #929298;
                font-size: 11px;
                padding: 2px 5px;
            }
            QTextBrowser {
                background: #171719;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 20px;
                padding: 12px;
                color: #F2F2F4;
                font-size: 13px;
                selection-background-color: #5E5CE6;
            }
            QLineEdit {
                background: #242427;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 17px;
                padding: 13px 15px;
                color: #F5F5F7;
                font-size: 13px;
                selection-background-color: #5E5CE6;
            }
            QLineEdit:focus { border: 1px solid rgba(142, 142, 255, 130); }
            QPushButton {
                background: #29292D;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 16px;
                padding: 10px 14px;
                color: #F5F5F7;
                font-size: 12px;
            }
            QPushButton:hover { background: #35353A; }
            QPushButton:disabled { color: #77777D; background: #202023; }
            QPushButton#quietButton {
                background: transparent;
                border: none;
                color: #A1A1A8;
                padding: 6px 8px;
            }
            QPushButton#sendButton {
                background: #F5F5F7;
                color: #161618;
                border: none;
                font-weight: 650;
                min-width: 42px;
            }
            QPushButton#voiceButton {
                background: #29292D;
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 17px;
                min-width: 42px;
                max-width: 42px;
                padding: 9px 0;
                font-size: 16px;
            }
            QPushButton#voiceButton[recording="true"] {
                background: #4A2024;
                border: 1px solid #9E424A;
                color: #FFB9C0;
            }
            QMenu {
                background: #202023;
                color: #F5F5F7;
                border: 1px solid #3B3B40;
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item { padding: 7px 22px; border-radius: 6px; }
            QMenu::item:selected { background: #3A3A40; }
        """)

        self._build_ui()
        self._set_compact_mode()
        if memory_status:
            self._append_message("System", memory_status)
        for item in self.brain.conversation.transcript():
            label = "You" if item["role"] == "user" else "Gennie"
            self._append_message(label, item["content"])
        self.refresh_state()
        self._place_initially()

    def _connect_wake_worker(self, worker: WakeWordWorker) -> None:
        worker.detected.connect(self.on_wake_word_detected)
        worker.status.connect(self._on_wake_status)
        worker.failed.connect(self._on_wake_error)
        worker.finished.connect(self._on_wake_listener_finished)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(3, 0, 3, 0)
        self.wordmark = QLabel("GENNIE")
        self.wordmark.setObjectName("wordmark")
        self.compact_button = QPushButton("Minimise")
        self.compact_button.setObjectName("quietButton")
        self.compact_button.clicked.connect(self.collapse)
        header_layout.addWidget(self.wordmark)
        header_layout.addStretch(1)
        header_layout.addWidget(self.compact_button)

        # The new sprite frames have larger, more expressive eyes and are
        # scaled with nearest-neighbour rendering to retain the pixel-art look.
        self.avatar = AvatarWidget(size=96)

        self.caption_label = QLabel()
        self.caption_label.setObjectName("caption")
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.hide()

        self.user_caption_label = QLabel()
        self.user_caption_label.setObjectName("userCaption")
        self.user_caption_label.setWordWrap(True)
        self.user_caption_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.user_caption_label.hide()

        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(False)
        self.history.setPlaceholderText("Your conversation with Gennie appears here.")

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.voice_button = QPushButton("●")
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setToolTip("Talk to Gennie. Press again to finish speaking.")
        self.voice_button.clicked.connect(self.toggle_voice_capture)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Message or speak to Gennie…")
        self.send_button = QPushButton("↑")
        self.send_button.setObjectName("sendButton")
        self.send_button.setToolTip("Send message")
        input_row.addWidget(self.voice_button)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_button)

        self.voice_status = QLabel("Local voice is ready when its models are installed.")
        self.voice_status.setObjectName("voiceStatus")
        self.voice_status.setWordWrap(True)

        outer.addWidget(self.header)
        outer.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self.user_caption_label)
        outer.addWidget(self.caption_label)
        outer.addWidget(self.history, 1)
        outer.addLayout(input_row)
        outer.addWidget(self.voice_status)

        self.send_button.clicked.connect(self.handle_input)
        self.input.returnPressed.connect(self.handle_input)

    def _append_message(self, speaker: str, text: str) -> None:
        safe = self._escape(text).replace("\n", "<br>")
        if speaker == "You":
            color = "#B8B8C0"
        elif speaker == "Gennie":
            color = "#E8E8F0"
        else:
            color = "#92929A"
        self.history.append(
            f'<p style="margin:8px 2px 2px 2px; line-height:1.45;">'
            f'<span style="color:{color}; font-weight:600;">{self._escape(speaker)}</span>'
            f'<br><span style="color:#E9E9ED;">{safe}</span></p>'
            '<hr style="border:0; border-top:1px solid #303034;">'
        )
        bar = self.history.verticalScrollBar()
        bar.setValue(bar.maximum())

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def _place_initially(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(available.right() - self.width() - 24, available.bottom() - self.height() - 24)

    def expand(self) -> None:
        if self._expanded:
            return
        self._stop_dormant_flight()
        self._voice_overlay = False
        self.user_caption_label.hide()
        self._expanded = True
        self.setFixedSize(*self.EXPANDED_SIZE)
        self.layout().setContentsMargins(15, 14, 15, 14)
        self.layout().setSpacing(10)
        self.compact_button.setText("Minimise")
        self.avatar.set_avatar_size(238)
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            x = min(self.x(), available.right() - self.width() - 18)
            y = min(self.y(), available.bottom() - self.height() - 18)
            self.move(max(available.left() + 18, x), max(available.top() + 18, y))
        for widget in (self.header, self.caption_label, self.history, self.input, self.send_button, self.voice_button, self.voice_status):
            widget.show()
        if self._unshown_voice_status:
            self.voice_status.setText(self._unshown_voice_status)
            self._unshown_voice_status = None
        self.input.setFocus()
        self.refresh_state()

    def expand_voice_overlay(self) -> None:
        """Show a small voice-session HUD instead of restoring the full chat log."""
        self._stop_dormant_flight()
        self._expanded = True
        self._voice_overlay = True
        self.setFixedSize(390, 310)
        self.layout().setContentsMargins(13, 12, 13, 12)
        self.layout().setSpacing(8)
        self.avatar.set_avatar_size(92)
        self.header.show()
        self.avatar.show()
        self.user_caption_label.show()
        self.caption_label.show()
        self.history.hide()
        self.input.hide()
        self.send_button.hide()
        self.voice_button.show()
        self.voice_status.show()
        self.compact_button.setText("Hide")
        if self._unshown_voice_status:
            self.voice_status.setText(self._unshown_voice_status)
            self._unshown_voice_status = None
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(min(self.x(), area.right() - self.width() - 16),
                      min(self.y(), area.bottom() - self.height() - 16))
        self.refresh_state()

    def collapse(self) -> None:
        if not self._expanded:
            return
        self._expanded = False
        self._voice_overlay = False
        self.user_caption_label.hide()
        self.setFixedSize(*self.COMPACT_SIZE)
        self.layout().setContentsMargins(6, 6, 6, 6)
        self.layout().setSpacing(0)
        self.avatar.set_avatar_size(96)
        for widget in (self.header, self.caption_label, self.history, self.input, self.send_button, self.voice_button, self.voice_status):
            widget.hide()
        self.clearFocus()
        self.refresh_state()
        if self.state_machine.is_state("SLEEPING"):
            self.start_dormant_flight()

    def _set_compact_mode(self) -> None:
        self._expanded = False
        self.setFixedSize(*self.COMPACT_SIZE)
        self.layout().setContentsMargins(6, 6, 6, 6)
        self.layout().setSpacing(0)
        self.avatar.set_avatar_size(96)
        for widget in (self.header, self.caption_label, self.history, self.input, self.send_button, self.voice_button, self.voice_status):
            widget.hide()

    def start_dormant_flight(self) -> None:
        """Let the tiny dormant genie wander between unhurried random waypoints."""
        if self._expanded or not self.state_machine.is_state("SLEEPING") or self._flight_timer.isActive():
            return
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is None:
            return
        self._flight_screen = screen.availableGeometry()
        self._flight_started = time.monotonic()
        self._flight_active = True
        self._flight_target = None
        self._flight_pause_until = self._flight_started + random.uniform(1.0, 2.2)
        self._flight_timer.start()

    def _stop_dormant_flight(self) -> None:
        self._flight_timer.stop()
        self._flight_active = False
        self._flight_target = None

    def _choose_dormant_waypoint(self, area) -> QPoint:
        margin = 22
        min_x = area.left() + margin
        max_x = max(min_x, area.right() - self.width() - margin)
        min_y = area.top() + margin
        max_y = max(min_y, area.bottom() - self.height() - margin)
        # Avoid tiny adjustments: each destination should feel like a deliberate
        # curious drift to another part of the desktop.
        for _ in range(8):
            point = QPoint(random.randint(min_x, max_x), random.randint(min_y, max_y))
            if (point - self.pos()).manhattanLength() > min(self.width() * 2, 150):
                return point
        return QPoint(random.randint(min_x, max_x), random.randint(min_y, max_y))

    def _update_dormant_flight(self) -> None:
        if self._expanded or not self.state_machine.is_state("SLEEPING"):
            self._stop_dormant_flight()
            return
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        now = time.monotonic()
        if self._flight_target is None:
            if now < self._flight_pause_until:
                return
            self._flight_target = self._choose_dormant_waypoint(area)

        delta = self._flight_target - self.pos()
        distance = (delta.x() ** 2 + delta.y() ** 2) ** 0.5
        if distance <= 7:
            self._flight_target = None
            self._flight_pause_until = now + random.uniform(2.5, 7.0)
            return

        # Slow, eased motion with a slight per-tick cap; no looping figure-eight.
        step = min(1.35, max(0.35, distance * 0.035))
        x = self.x() + (delta.x() / distance) * step
        y = self.y() + (delta.y() / distance) * step
        margin = 22
        x = min(area.right() - self.width() - margin, max(area.left() + margin, round(x)))
        y = min(area.bottom() - self.height() - margin, max(area.top() + margin, round(y)))
        self.move(x, y)

    def refresh_state(self) -> None:
        self.avatar.set_state(self.state_machine.current_state)
        if self.state_machine.is_state("SLEEPING") and not self._expanded:
            self.start_dormant_flight()
        else:
            self._stop_dormant_flight()

    def _on_wake_status(self, message: str) -> None:
        self.voice_status.setText(message)
        if self._expanded:
            self._append_message("Voice", message)
        else:
            self._unshown_voice_status = message

    def _on_wake_error(self, message: str) -> None:
        self.voice_status.setText(message)
        if self._expanded:
            self._append_message("Voice", message)
        else:
            self._unshown_voice_status = message

    def on_wake_word_detected(self, keyword: str) -> None:
        """Summon Gennie, release the wake-listener microphone, then record speech."""
        if self.state_machine.current_state not in {"SLEEPING", "IDLE"} or self._worker is not None:
            return
        self._pending_voice_capture = True
        self._voice_session_active = True
        self._emergence_complete = False
        self._final_transcript = ""
        self.activate_from_lamp(source="wake word")

    def _on_wake_listener_finished(self) -> None:
        # WakeWordWorker exits immediately after a match, releasing the input
        # stream before SpeechRecognitionWorker opens the same microphone.
        self._maybe_start_voice_capture()

    def _stop_wake_listener(self) -> None:
        if self.wake_worker is not None and self.wake_worker.isRunning():
            self.wake_worker.requestInterruption()

    def _arm_wake_listener(self) -> None:
        if not self._wake_enabled or self.wake_worker is None:
            return
        if self.state_machine.current_state != "SLEEPING":
            return
        if self._worker is not None or self._voice_worker is not None:
            return
        if not self.wake_worker.isRunning():
            self.wake_worker.start()

    def activate_from_lamp(self, source: str = "manual") -> None:
        self._inactivity_timer.stop()
        if self.state_machine.current_state in {"SLEEPING", "IDLE"}:
            self.state_machine.change_state("EMERGING")
        else:
            return
        self.refresh_state()
        if source in {"wake word", "microphone"}:
            self.expand_voice_overlay()
        elif not self._expanded:
            self.expand()
        self._summon_timer.start(1250)
        if source == "wake word":
            self.show_assistant_subtitle("I'm listening.")
            self.voice_status.setText("Wake word detected · listening for your request")
        else:
            self.show_assistant_subtitle("I'm here.")

    def _finish_emergence(self) -> None:
        if self.state_machine.is_state("EMERGING"):
            self.state_machine.change_state("LISTENING")
            self.refresh_state()
            self._emergence_complete = True
            if self._pending_voice_capture:
                self._maybe_start_voice_capture()
            else:
                QTimer.singleShot(650, self._settle_to_idle)

    def _settle_to_idle(self) -> None:
        if self.state_machine.is_state("LISTENING") and self._voice_worker is None:
            self.state_machine.change_state("IDLE")
            self.refresh_state()
            self._inactivity_timer.start(self._idle_timeout_ms)

    def _return_to_lamp(self) -> None:
        if self.state_machine.current_state not in {"IDLE", "SPEAKING"}:
            return
        if self._speech_worker is not None and self._speech_worker.isRunning():
            self._speech_worker.stop()
        if self.state_machine.is_state("SPEAKING"):
            self.state_machine.change_state("IDLE")
        self.state_machine.change_state("RETURNING")
        self.refresh_state()
        self._return_timer.start(1150)

    def _finish_return(self) -> None:
        if self.state_machine.is_state("RETURNING"):
            self.state_machine.change_state("SLEEPING")
            self.refresh_state()
            self._assistant_caption_timer.stop()
            self.caption_label.clear()
            self.caption_label.hide()
            self.collapse()
            self._arm_wake_listener()

    def show_user_subtitle(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        self.user_caption_label.setText(f"You · {cleaned}")
        self.user_caption_label.show()

    def show_assistant_subtitle(self, text: str, duration_ms: int = 6500) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        self.caption_label.setText(cleaned)
        self.caption_label.show()
        self._assistant_caption_timer.start(duration_ms)

    def _clear_assistant_caption(self) -> None:
        self.caption_label.clear()
        self.caption_label.hide()

    def toggle_voice_capture(self) -> None:
        if self._voice_worker is not None and self._voice_worker.isRunning():
            self.voice_status.setText("Finishing your sentence…")
            self.voice_button.setText("…")
            self._voice_worker.request_stop()
            return
        if self._worker is not None:
            self.voice_status.setText("Gennie is finishing the current reply first.")
            return

        self._inactivity_timer.stop()
        self._stop_speech_output()
        if self._expanded and not self._voice_overlay:
            self.expand_voice_overlay()
        self._voice_session_active = True
        self._pending_voice_capture = True
        self._emergence_complete = False
        self._final_transcript = ""

        if self.state_machine.current_state in {"SLEEPING", "IDLE"}:
            self.activate_from_lamp(source="microphone")
        elif self.state_machine.is_state("SPEAKING"):
            self.state_machine.change_state("IDLE")
            self.state_machine.change_state("LISTENING")
            self._emergence_complete = True
            self.refresh_state()
        elif self.state_machine.is_state("THINKING"):
            self._pending_voice_capture = False
            return
        elif self.state_machine.is_state("EMERGING"):
            self._emergence_complete = False
        elif self.state_machine.is_state("RETURNING"):
            self._return_timer.stop()
            self.state_machine.change_state("IDLE")
            self.state_machine.change_state("LISTENING")
            self._emergence_complete = True
            self.refresh_state()
        elif self.state_machine.is_state("IDLE"):
            self.state_machine.change_state("LISTENING")
            self._emergence_complete = True
            self.refresh_state()
        elif self.state_machine.is_state("LISTENING"):
            self._emergence_complete = True

        self._stop_wake_listener()
        self._maybe_start_voice_capture()

    def _maybe_start_voice_capture(self) -> None:
        if not self._pending_voice_capture:
            return
        if self.wake_worker is not None and self.wake_worker.isRunning():
            return
        if self._voice_worker is not None and self._voice_worker.isRunning():
            return
        if self.state_machine.current_state not in {"EMERGING", "LISTENING", "IDLE"}:
            return
        # Begin capture as soon as the wake thread releases the microphone;
        # let the visual emergence animation continue in parallel. This avoids
        # dropping the start of a sentence spoken immediately after the name.
        self._pending_voice_capture = False
        self._start_voice_capture()

    def _start_voice_capture(self) -> None:
        if self._worker is not None:
            return
        self._final_transcript = ""
        self._voice_error = ""
        self.input.clear()
        self.input.setPlaceholderText("Listening… your words will appear here")
        self.voice_button.setText("■")
        self.voice_button.setProperty("recording", True)
        self.voice_button.style().unpolish(self.voice_button)
        self.voice_button.style().polish(self.voice_button)
        self.voice_status.setText("Listening · speak naturally; silence ends your turn")
        if not self.state_machine.is_state("LISTENING"):
            try:
                if self.state_machine.is_state("IDLE"):
                    self.state_machine.change_state("LISTENING")
                elif self.state_machine.is_state("SPEAKING"):
                    self.state_machine.change_state("IDLE")
                    self.state_machine.change_state("LISTENING")
            except InvalidTransitionError:
                pass
        self.refresh_state()

        self._voice_worker = SpeechRecognitionWorker(parent=self)
        self._voice_worker.partial_text.connect(self._on_partial_transcript)
        self._voice_worker.final_text.connect(self._on_final_transcript)
        self._voice_worker.status.connect(self.voice_status.setText)
        self._voice_worker.failed.connect(self._on_voice_failure)
        self._voice_worker.finished.connect(self._on_voice_worker_finished)
        self._voice_worker.start()

    def _on_partial_transcript(self, text: str) -> None:
        # QLineEdit renders each incoming hypothesis like live typing, including
        # revisions the recognizer makes as it hears more of the sentence.
        self.input.setText(text)
        self.input.setCursorPosition(len(text))
        self.voice_status.setText("Hearing you…")

    def _on_final_transcript(self, text: str) -> None:
        self._final_transcript = text.strip()
        if self._final_transcript:
            self.input.setText(self._final_transcript)
            self.input.setCursorPosition(len(self._final_transcript))
            if self._voice_overlay:
                self.show_user_subtitle(self._final_transcript)

    def _on_voice_failure(self, message: str) -> None:
        self._voice_error = message
        self.voice_status.setText(message)

    def _on_voice_worker_finished(self) -> None:
        worker = self._voice_worker
        self._voice_worker = None
        self.voice_button.setText("●")
        self.voice_button.setProperty("recording", False)
        self.voice_button.style().unpolish(self.voice_button)
        self.voice_button.style().polish(self.voice_button)
        self.input.setPlaceholderText("Message or speak to Gennie…")
        if worker is not None:
            worker.deleteLater()

        transcript = self._final_transcript.strip()
        if transcript:
            self.input.setText(transcript)
            if not self._voice_overlay:
                self._append_message("You", transcript)
            # Submit after the capture thread has fully released the microphone.
            QTimer.singleShot(80, self._submit_recognised_speech)
        else:
            self.voice_status.setText(self._voice_error or "I didn't catch that. Try again or type your message.")
            self._voice_session_active = False
            if self.state_machine.is_state("LISTENING"):
                self.state_machine.change_state("IDLE")
                self.refresh_state()
                self._inactivity_timer.start(min(self._idle_timeout_ms, 15_000))

    def _submit_recognised_speech(self) -> None:
        if self.input.text().strip() and self._worker is None:
            self.handle_input(already_logged=True)

    def show_conversation(self) -> None:
        if self.state_machine.is_state("SLEEPING"):
            self.activate_from_lamp(source="manual")
        else:
            self.expand()

    def handle_input(self, already_logged: bool = False) -> None:
        message = self.input.text().strip()
        if not message or self._worker is not None or self._voice_worker is not None:
            return

        self._stop_wake_listener()
        self._stop_speech_output()
        self._inactivity_timer.stop()
        self.input.clear()
        if not already_logged:
            self._append_message("You", message)
        command = message.strip()

        if command.startswith("/"):
            self._show_local_reply(self._handle_local_command(command))
            return

        natural_forget = re.match(r"^(?:please\s+)?forget\s+(.+)$", command, flags=re.IGNORECASE)
        if natural_forget:
            self._show_local_reply(self._forget_memory_phrase(natural_forget.group(1).strip()))
            return

        try:
            if self.state_machine.is_state("SLEEPING"):
                self.state_machine.change_state("IDLE")
            if self.state_machine.is_state("EMERGING"):
                self.state_machine.change_state("LISTENING")
            elif self.state_machine.is_state("SPEAKING"):
                self.state_machine.change_state("IDLE")
                self.state_machine.change_state("LISTENING")
            elif self.state_machine.is_state("IDLE"):
                self.state_machine.change_state("LISTENING")
            if self.state_machine.is_state("LISTENING"):
                self.state_machine.change_state("THINKING")
            self.refresh_state()
        except (InvalidTransitionError, ValueError) as exc:
            self._show_local_reply(f"I couldn't start that turn: {exc}")
            return

        self.input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.voice_button.setEnabled(False)
        self.send_button.setText("…")
        self._worker = ChatWorker(self.brain, self.memory, message)
        self._worker.succeeded.connect(self._on_chat_success)
        self._worker.failed.connect(self._on_chat_failure)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _handle_local_command(self, command: str) -> str:
        lowered = command.casefold()
        if lowered == "/help":
            return "Commands: /status, /sleep, /wake, /memories, /remember <fact>, /forget <phrase>, /clear."
        if lowered == "/status":
            db_status = "connected" if self.memory.store.available else "offline"
            return f"State: {self.state_machine.current_state}. Model: {self.brain.provider.model}. Memory: {db_status}."
        if lowered == "/sleep":
            if self.state_machine.current_state in {"IDLE", "SPEAKING", "LISTENING"}:
                if self.state_machine.is_state("SPEAKING") or self.state_machine.is_state("LISTENING"):
                    self.state_machine.change_state("IDLE")
                self.state_machine.change_state("RETURNING")
                self.refresh_state()
                self._return_timer.start(1150)
            return "Back to my lamp."
        if lowered == "/wake":
            if self.state_machine.is_state("SLEEPING"):
                self.activate_from_lamp(source="command")
            return "I was only pretending to nap."
        if lowered == "/clear":
            new_id = str(uuid4())
            try:
                self.memory.store.create_conversation(new_id)
            except Exception as exc:
                return f"I couldn't start a fresh conversation: {exc}"
            self.brain.conversation.conversation_id = new_id
            self.brain.conversation.messages.clear()
            self.history.clear()
            return "Fresh conversation started. Older saved memories remain in PostgreSQL."
        if lowered == "/memories":
            if not self.memory.store.available:
                return "My memory database is offline. Connect PostgreSQL before using long-term memory."
            try:
                memories = self.memory.list_memories()
            except Exception as exc:
                return f"I couldn't read my memories: {exc}"
            if not memories:
                return "Nothing saved yet. Use /remember followed by a fact to save one."
            return "Here's what I remember:\n" + "\n".join(
                f"- {item['content']}" for item in memories
            )
        if lowered.startswith("/remember"):
            fact = command[len("/remember"):].strip()
            if not fact:
                return "Use /remember followed by the fact you want me to retain."
            try:
                self.memory.remember_explicit(fact)
                return "Saved to long-term memory."
            except Exception as exc:
                return f"I couldn't save that memory: {exc}"
        if lowered.startswith("/forget"):
            phrase = command[len("/forget"):].strip()
            if not phrase:
                return "Use /forget followed by a phrase to find memories to delete."
            return self._forget_memory_phrase(phrase)
        return "I don't recognise that command. Type /help for the available commands."

    def _forget_memory_phrase(self, phrase: str) -> str:
        if not phrase:
            return "Tell me what you want me to forget."
        try:
            count = self.memory.forget(phrase)
            return f"Forgot {count} matching memory entr{'y' if count == 1 else 'ies'}."
        except Exception as exc:
            return f"I couldn't update memory: {exc}"

    def _show_local_reply(self, reply: str) -> None:
        try:
            if self.state_machine.is_state("SLEEPING"):
                self.state_machine.change_state("IDLE")
            if self.state_machine.is_state("SPEAKING"):
                self.state_machine.change_state("IDLE")
            if self.state_machine.is_state("IDLE"):
                self.state_machine.change_state("LISTENING")
            if self.state_machine.is_state("LISTENING"):
                self.state_machine.change_state("THINKING")
            if self.state_machine.is_state("THINKING"):
                self.state_machine.change_state("SPEAKING")
        except InvalidTransitionError:
            pass
        self.refresh_state()
        self.show_assistant_subtitle(reply, max(6500, min(16000, len(reply) * 70)))
        if not self._voice_overlay:
            self._append_message("Gennie", reply)
        self._speak_reply(reply)

    def _on_chat_success(self, reply: str) -> None:
        if self.state_machine.is_state("THINKING"):
            self.state_machine.change_state("SPEAKING")
        self.refresh_state()
        self.show_assistant_subtitle(reply, max(6500, min(16000, len(reply) * 70)))
        if not self._voice_overlay:
            self._append_message("Gennie", reply)
        self._speak_reply(reply)

    def _on_chat_failure(self, error: str) -> None:
        if self.state_machine.is_state("THINKING"):
            self.state_machine.change_state("ERROR")
        self.refresh_state()
        message = f"I couldn't complete that turn. {error}"
        self.show_assistant_subtitle(message)
        if not self._voice_overlay:
            self._append_message("System", message)
        QTimer.singleShot(1300, self._recover_from_error)

    def _recover_from_error(self) -> None:
        if self.state_machine.is_state("ERROR"):
            self.state_machine.change_state("BOOTING")
            self.state_machine.change_state("IDLE")
            self.refresh_state()
            if self._voice_session_active:
                QTimer.singleShot(500, self._begin_followup_voice_capture)
            else:
                self._inactivity_timer.start(self._idle_timeout_ms)

    def _speak_reply(self, reply: str) -> None:
        if not self._tts_enabled or platform.system() != "Darwin":
            QTimer.singleShot(450, self._finish_speaking)
            return
        if self._speech_worker is not None and self._speech_worker.isRunning():
            self._speech_worker.stop()
        self._speech_worker = SpeechOutputWorker(reply, parent=self)
        self._speech_worker.failed.connect(self._on_speech_error)
        self._speech_worker.voice_selected.connect(
            lambda voice: self.voice_status.setText(f"Speaking with {voice}.")
        )
        self._speech_worker.finished.connect(self._on_speech_finished)
        self._speech_worker.start()

    def _stop_speech_output(self) -> None:
        if self._speech_worker is not None and self._speech_worker.isRunning():
            self._speech_worker.stop()

    def _on_speech_error(self, message: str) -> None:
        self.voice_status.setText(message)

    def _on_speech_finished(self) -> None:
        worker = self._speech_worker
        self._speech_worker = None
        if worker is not None:
            worker.deleteLater()
        self._finish_speaking()

    def _on_worker_finished(self) -> None:
        self.input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.voice_button.setEnabled(True)
        self.send_button.setText("↑")
        if self._expanded:
            self.input.setFocus()
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

    def _finish_speaking(self) -> None:
        if self.state_machine.is_state("SPEAKING"):
            self.state_machine.change_state("IDLE")
            self.refresh_state()
            if self._voice_session_active:
                self.voice_status.setText("Ready for your next prompt")
                QTimer.singleShot(350, self._begin_followup_voice_capture)
            else:
                self._inactivity_timer.start(self._idle_timeout_ms)

    def _begin_followup_voice_capture(self) -> None:
        """Keep a voice conversation open after each spoken assistant reply."""
        if not self._voice_session_active or self._voice_worker is not None:
            return
        if self._worker is not None:
            QTimer.singleShot(250, self._begin_followup_voice_capture)
            return
        if self._speech_worker is not None and self._speech_worker.isRunning():
            QTimer.singleShot(250, self._begin_followup_voice_capture)
            return
        if self.state_machine.is_state("IDLE"):
            self.state_machine.change_state("LISTENING")
        if self.state_machine.is_state("LISTENING"):
            self._pending_voice_capture = True
            self._emergence_complete = True
            self._maybe_start_voice_capture()

    @staticmethod
    def _escape(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if not self._expanded:
                self._stop_dormant_flight()
                self._compact_press_global = global_pos
                self._compact_was_dragged = False
                self._drag_offset = global_pos - self.frameGeometry().topLeft()
                event.accept()
                return
            if event.position().y() < 52:
                self._drag_offset = global_pos - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if not self._expanded and self._compact_press_global is not None:
                distance = (global_pos - self._compact_press_global).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    self._compact_was_dragged = True
            if self._expanded or self._compact_was_dragged:
                self.move(global_pos - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._expanded:
            should_expand = not self._compact_was_dragged
            self._drag_offset = None
            self._compact_press_global = None
            if should_expand:
                self.expand()
                if self.state_machine.is_state("SLEEPING"):
                    self.activate_from_lamp(source="manual")
            elif self.state_machine.is_state("SLEEPING"):
                self.start_dormant_flight()
            event.accept()
            return
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self._expanded:
            self.collapse()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_dormant_flight()
        super().closeEvent(event)

    def contextMenuEvent(self, event) -> None:
        self._show_context_menu(event.globalPos())

    def _show_context_menu(self, position) -> None:
        menu = QMenu(self)
        mode_action = QAction("Show conversation" if not self._expanded else "Minimise", self)
        mode_action.triggered.connect(self.show_conversation if not self._expanded else self.collapse)
        menu.addAction(mode_action)
        menu.addSeparator()
        quit_action = QAction("Quit Project Gennie", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        menu.exec(position)
