"""Minimal character-first desktop companion window."""

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.core.state_machine import InvalidTransitionError, StateMachine
from app.ui.avatar import AvatarWidget


class MainWindow(QWidget):
    COMPACT_SIZE = (260, 320)
    EXPANDED_SIZE = (540, 760)

    def __init__(self, state_machine: StateMachine) -> None:
        super().__init__()
        self.state_machine = state_machine
        self._expanded = False
        self._drag_offset: QPoint | None = None
        self._compact_press_global: QPoint | None = None
        self._compact_was_dragged = False
        self._assistant_caption_timer = QTimer(self)
        self._assistant_caption_timer.setSingleShot(True)
        self._assistant_caption_timer.timeout.connect(self._clear_assistant_caption)
        self._user_transcript_timer = QTimer(self)
        self._user_transcript_timer.setSingleShot(True)
        self._user_transcript_timer.timeout.connect(self._clear_user_transcript)

        self.setWindowTitle("Tuna")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("windowRoot")
        self.setStyleSheet("""
            QWidget#windowRoot {
                background: #13232a;
                border: 1px solid #31515a;
                border-radius: 22px;
                color: #e8f4f1;
            }
            QLabel { color: #e8f4f1; }
            QLabel#wordmark { color: #b9e9df; font-size: 11px; font-weight: 700; letter-spacing: 3px; }
            QLabel#stateLabel { color: #8bb8b1; font-size: 10px; letter-spacing: 2px; }
            QLabel#caption, QLabel#transcript {
                background: #1b3038;
                border: 1px solid #29454d;
                border-radius: 11px;
                padding: 9px 12px;
                color: #e5f1ed;
                font-size: 12px;
            }
            QLabel#transcript { color: #a8d6ce; }
            QTextBrowser {
                background: #0e1b20;
                border: 1px solid #29454d;
                border-radius: 12px;
                padding: 10px;
                color: #e5f1ed;
                font-size: 12px;
            }
            QLineEdit {
                background: #0e1b20;
                border: 1px solid #3b6269;
                border-radius: 10px;
                padding: 10px 12px;
                color: #f4fbf8;
                selection-background-color: #367f78;
            }
            QPushButton {
                background: #25444a;
                border: 1px solid #3c6867;
                border-radius: 10px;
                padding: 8px 12px;
                color: #e8f4f1;
            }
            QPushButton:hover { background: #315a5e; }
            QPushButton#quietButton { background: transparent; border: none; color: #9cc8c1; }
            QPushButton#sendButton { background: #377d74; border: none; font-weight: 600; }
        """)

        self._build_ui()
        self._set_compact_mode()
        self.refresh_state()
        self._place_initially()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 14)
        outer.setSpacing(8)

        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.wordmark = QLabel("T U N A")
        self.wordmark.setObjectName("wordmark")
        self.compact_button = QPushButton("Compact")
        self.compact_button.setObjectName("quietButton")
        self.compact_button.clicked.connect(self.collapse)
        header_layout.addWidget(self.wordmark)
        header_layout.addStretch(1)
        header_layout.addWidget(self.compact_button)

        self.avatar = AvatarWidget(size=140)
        self.state_label = QLabel("IDLE")
        self.state_label.setObjectName("stateLabel")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.transcript_label = QLabel()
        self.transcript_label.setObjectName("transcript")
        self.transcript_label.setWordWrap(True)
        self.transcript_label.hide()

        self.caption_label = QLabel("Tap Tuna to open the conversation")
        self.caption_label.setObjectName("caption")
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(False)
        self.history.setPlaceholderText("Your conversation will appear here.")
        self.history.append("<b>Tuna</b> · Hey. I'm here.")

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Message Tuna…")
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_button)

        self.footer_hint = QLabel("CLICK TO OPEN")
        self.footer_hint.setObjectName("stateLabel")
        self.footer_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(self.header)
        outer.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self.state_label)
        outer.addWidget(self.transcript_label)
        outer.addWidget(self.caption_label)
        outer.addWidget(self.history, 1)
        outer.addLayout(input_row)
        outer.addWidget(self.footer_hint)

        self.send_button.clicked.connect(self.handle_input)
        self.input.returnPressed.connect(self.handle_input)

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def _place_initially(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(
            available.right() - self.width() - 24,
            available.bottom() - self.height() - 24,
        )

    def expand(self) -> None:
        if self._expanded:
            return
        self._expanded = True
        self.setFixedSize(*self.EXPANDED_SIZE)
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            x = min(self.x(), available.right() - self.width() - 20)
            y = min(self.y(), available.bottom() - self.height() - 20)
            self.move(max(available.left() + 20, x), max(available.top() + 20, y))
        self.header.show()
        self.history.show()
        self.input.show()
        self.send_button.show()
        self.footer_hint.hide()
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.input.setFocus()
        self.refresh_state()

    def collapse(self) -> None:
        if not self._expanded:
            return
        self._expanded = False
        self.setFixedSize(*self.COMPACT_SIZE)
        self.header.hide()
        self.history.hide()
        self.input.hide()
        self.send_button.hide()
        self.footer_hint.show()
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clearFocus()
        self.refresh_state()

    def _set_compact_mode(self) -> None:
        self._expanded = False
        self.setFixedSize(*self.COMPACT_SIZE)
        self.header.hide()
        self.history.hide()
        self.input.hide()
        self.send_button.hide()
        self.footer_hint.show()
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def refresh_state(self) -> None:
        state = self.state_machine.current_state
        self.state_label.setText(state)
        self.avatar.set_state(state)

    def show_assistant_subtitle(self, text: str, duration_ms: int = 6500) -> None:
        """Display a short assistant caption; a future TTS service can call this."""
        self.caption_label.setText(text)
        self.caption_label.show()
        self._assistant_caption_timer.start(duration_ms)

    def show_user_transcription(self, text: str, duration_ms: int = 6500) -> None:
        """Display recognised speech; a future local STT service can call this."""
        self.transcript_label.setText(f"YOU  ·  {text}")
        self.transcript_label.show()
        self._user_transcript_timer.start(duration_ms)

    def _clear_assistant_caption(self) -> None:
        if not self._expanded:
            self.caption_label.setText("Tap Tuna to open the conversation")
        else:
            self.caption_label.setText(" ")

    def _clear_user_transcript(self) -> None:
        self.transcript_label.hide()
        self.transcript_label.clear()

    def handle_input(self) -> None:
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.history.append(f"<b>You</b> · {self._escape(message)}")

        try:
            if self.state_machine.is_state("SLEEPING"):
                if message.lower() == "/wake":
                    self.state_machine.change_state("IDLE")
                    self.state_machine.change_state("LISTENING")
                    self.state_machine.change_state("THINKING")
                    reply = "I'm back."
                else:
                    reply = "I'm sleeping. Type /wake to wake me."
                    self.show_assistant_subtitle(reply)
                    self.history.append(f"<b>Tuna</b> · {self._escape(reply)}")
                    return
            else:
                if self.state_machine.is_state("SPEAKING"):
                    self.state_machine.change_state("IDLE")
                self.state_machine.change_state("LISTENING")
                self.refresh_state()
                self.state_machine.change_state("THINKING")
                self.refresh_state()
                reply = self._respond(message)

            if self.state_machine.is_state("SLEEPING"):
                self.show_assistant_subtitle(reply)
                self.history.append(f"<b>Tuna</b> · {self._escape(reply)}")
                return

            self.state_machine.change_state("SPEAKING")
            self.refresh_state()
            self.show_assistant_subtitle(reply)
            self.history.append(f"<b>Tuna</b> · {self._escape(reply)}")
            QTimer.singleShot(900, self._finish_speaking)
        except (InvalidTransitionError, ValueError) as exc:
            try:
                if not self.state_machine.is_state("ERROR"):
                    self.state_machine.change_state("ERROR")
            except (InvalidTransitionError, ValueError):
                pass
            self.history.append(f"<b>System</b> · {self._escape(str(exc))}")
        finally:
            self.refresh_state()
            self.history.verticalScrollBar().setValue(
                self.history.verticalScrollBar().maximum()
            )

    def _respond(self, message: str) -> str:
        command = message.strip().lower()
        if command == "/help":
            return "Try /help, /status, /sleep, /wake, /clear or /demo."
        if command == "/status":
            return f"My current state is {self.state_machine.current_state}."
        if command == "/sleep":
            self.state_machine.change_state("IDLE")
            self.state_machine.change_state("SLEEPING")
            return "Night. I'll be here when you wake me."
        if command == "/wake":
            return "I'm already awake."
        if command == "/clear":
            self.history.clear()
            return "Conversation cleared."
        if command == "/demo":
            self.show_user_transcription("Hey Tuna, can you hear me?")
            return "Loud and clear. Voice features are not connected yet, but this is where my captions will appear."
        return (
            "I got your message. I'm still using a placeholder reply; my AI brain "
            "hasn't been connected yet."
        )

    def _finish_speaking(self) -> None:
        if self.state_machine.is_state("SPEAKING"):
            self.state_machine.change_state("IDLE")
            self.refresh_state()

    @staticmethod
    def _escape(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if not self._expanded:
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
            event.accept()
            return
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self._expanded:
            self.collapse()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event) -> None:
        self._show_context_menu(event.globalPos())

    def _show_context_menu(self, position) -> None:
        menu = QMenu(self)
        mode_action = QAction("Show conversation" if not self._expanded else "Compact Tuna", self)
        mode_action.triggered.connect(self.expand if not self._expanded else self.collapse)
        menu.addAction(mode_action)
        menu.addSeparator()
        quit_action = QAction("Quit Tuna", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        menu.exec(position)
