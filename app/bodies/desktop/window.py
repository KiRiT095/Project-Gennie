"""Minimal, character-first desktop companion window."""

from __future__ import annotations

import re
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

from app.brain.brain import TunaBrain
from app.bodies.desktop.chat_worker import ChatWorker
from app.core.state_machine import InvalidTransitionError, StateMachine
from app.memory.manager import MemoryManager
from app.ui.avatar import AvatarWidget


class MainWindow(QWidget):
    COMPACT_SIZE = (224, 224)
    EXPANDED_SIZE = (520, 720)

    def __init__(
        self,
        state_machine: StateMachine,
        brain: TunaBrain,
        memory: MemoryManager,
        memory_status: str = "",
    ) -> None:
        super().__init__()
        self.state_machine = state_machine
        self.brain = brain
        self.memory = memory
        self.memory_status = memory_status
        self._worker: ChatWorker | None = None
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
                background: rgba(15, 22, 25, 238);
                border: 1px solid rgba(74, 116, 119, 150);
                border-radius: 24px;
                color: #e8f4f1;
            }
            QLabel { color: #e8f4f1; }
            QLabel#wordmark {
                color: #b9e9df;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 3px;
            }
            QLabel#caption, QLabel#transcript {
                background: rgba(27, 48, 56, 238);
                border: 1px solid #29454d;
                border-radius: 12px;
                padding: 9px 12px;
                color: #e5f1ed;
                font-size: 12px;
            }
            QLabel#transcript { color: #a8d6ce; }
            QTextBrowser {
                background: rgba(14, 27, 32, 245);
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
            QPushButton#quietButton {
                background: transparent;
                border: none;
                color: #9cc8c1;
            }
            QPushButton#sendButton {
                background: #377d74;
                border: none;
                font-weight: 600;
            }
        """)

        self._build_ui()
        self._set_compact_mode()
        if memory_status:
            self.history.append(f"<i>System</i> · {self._escape(memory_status)}")
        for item in self.brain.conversation.transcript():
            label = "You" if item["role"] == "user" else "Tuna"
            self.history.append(f"<b>{label}</b> · {self._escape(item['content'])}")
        self.refresh_state()
        self._place_initially()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(9)

        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(2, 0, 2, 0)
        self.wordmark = QLabel("T U N A")
        self.wordmark.setObjectName("wordmark")
        self.compact_button = QPushButton("Compact")
        self.compact_button.setObjectName("quietButton")
        self.compact_button.clicked.connect(self.collapse)
        header_layout.addWidget(self.wordmark)
        header_layout.addStretch(1)
        header_layout.addWidget(self.compact_button)

        self.avatar = AvatarWidget(size=188)

        self.transcript_label = QLabel()
        self.transcript_label.setObjectName("transcript")
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_label.hide()

        self.caption_label = QLabel()
        self.caption_label.setObjectName("caption")
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.hide()

        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(False)
        self.history.setPlaceholderText("Your conversation with Tuna will appear here.")

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Message Tuna…")
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_button)

        outer.addWidget(self.header)
        outer.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self.transcript_label)
        outer.addWidget(self.caption_label)
        outer.addWidget(self.history, 1)
        outer.addLayout(input_row)

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
            available.right() - self.width() - 28,
            available.bottom() - self.height() - 28,
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
        self.clearFocus()
        self.refresh_state()
        self._fit_compact_height()

    def _set_compact_mode(self) -> None:
        self._expanded = False
        self.setFixedSize(*self.COMPACT_SIZE)
        self.header.hide()
        self.history.hide()
        self.input.hide()
        self.send_button.hide()

    def refresh_state(self) -> None:
        """Reflect the internal state through the character, not a text label."""
        self.avatar.set_state(self.state_machine.current_state)

    def show_assistant_subtitle(self, text: str, duration_ms: int = 6500) -> None:
        """Show a temporary caption when Tuna has something to say."""
        cleaned = text.strip()
        if not cleaned:
            return
        self.caption_label.setText(cleaned)
        self.caption_label.show()
        self._assistant_caption_timer.start(duration_ms)
        self._fit_compact_height()

    def show_user_transcription(self, text: str, duration_ms: int = 6500) -> None:
        """Show a temporary transcript when a speech-to-text service supplies it."""
        cleaned = text.strip()
        if not cleaned:
            return
        self.transcript_label.setText(cleaned)
        self.transcript_label.show()
        self._user_transcript_timer.start(duration_ms)
        self._fit_compact_height()

    def _fit_compact_height(self) -> None:
        """Grow only while a temporary caption is visible; keep the bottom anchored."""
        if self._expanded:
            return
        layout = self.layout()
        if layout is None:
            return
        layout.activate()
        required_height = max(self.COMPACT_SIZE[1], layout.sizeHint().height() + 4)
        if required_height == self.height():
            return
        bottom = self.frameGeometry().bottom()
        self.setFixedSize(self.COMPACT_SIZE[0], required_height)
        self.move(self.x(), bottom - self.height() + 1)

    def _clear_assistant_caption(self) -> None:
        self.caption_label.clear()
        self.caption_label.hide()
        self._fit_compact_height()

    def _clear_user_transcript(self) -> None:
        self.transcript_label.clear()
        self.transcript_label.hide()
        self._fit_compact_height()

    def handle_input(self) -> None:
        message = self.input.text().strip()
        if not message or self._worker is not None:
            return

        self.input.clear()
        self.history.append(f"<b>You</b> · {self._escape(message)}")
        command = message.strip()

        if self.state_machine.is_state("SLEEPING"):
            if command.lower() == "/wake":
                self.state_machine.change_state("IDLE")
                self._show_local_reply("I'm back.")
            else:
                self._show_local_reply("I'm sleeping. Type /wake to wake me.")
            return

        if command.startswith("/"):
            reply = self._handle_local_command(command)
            self._show_local_reply(reply)
            return

        natural_forget = re.match(r"^(?:please\s+)?forget\s+(.+)$", command, flags=re.IGNORECASE)
        if natural_forget:
            reply = self._forget_memory_phrase(natural_forget.group(1).strip())
            self._show_local_reply(reply)
            return

        try:
            if self.state_machine.is_state("SPEAKING"):
                self.state_machine.change_state("IDLE")
            self.state_machine.change_state("LISTENING")
            self.refresh_state()
            self.state_machine.change_state("THINKING")
            self.refresh_state()
        except (InvalidTransitionError, ValueError) as exc:
            self._show_local_reply(f"I couldn't start that turn: {exc}")
            return

        self.input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("Thinking…")
        self._worker = ChatWorker(self.brain, self.memory, message)
        self._worker.succeeded.connect(self._on_chat_success)
        self._worker.failed.connect(self._on_chat_failure)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        self.history.verticalScrollBar().setValue(
            self.history.verticalScrollBar().maximum()
        )

    def _handle_local_command(self, command: str) -> str:
        lowered = command.casefold()
        if lowered == "/help":
            return (
                "Commands: /status, /sleep, /wake, /memories, "
                "/remember <fact>, /forget <phrase>, /clear, /demo."
            )
        if lowered == "/status":
            db_status = "connected" if self.memory.store.available else "offline"
            return f"State: {self.state_machine.current_state}. Model: {self.brain.provider.model}. Memory database: {db_status}."
        if lowered == "/sleep":
            if self.state_machine.is_state("SPEAKING"):
                self.state_machine.change_state("IDLE")
            self.state_machine.change_state("SLEEPING")
            self.refresh_state()
            return "Night. I'll be here when you wake me."
        if lowered == "/wake":
            return "I'm already awake."
        if lowered == "/clear":
            new_id = str(uuid4())
            try:
                self.memory.store.create_conversation(new_id)
            except Exception as exc:
                return f"I couldn't start a fresh conversation: {exc}"
            self.brain.conversation.conversation_id = new_id
            self.brain.conversation.messages.clear()
            self.history.clear()
            return "Fresh conversation started. Older chat history and saved memories remain in PostgreSQL."
        if lowered == "/demo":
            self.show_user_transcription("Hey Tuna, can you hear me?")
            return "Loud and clear. This is a preview of where voice captions will appear."
        if lowered == "/memories":
            if not self.memory.store.available:
                return "My memory database is offline. Connect PostgreSQL before using long-term memory."
            try:
                memories = self.memory.list_memories()
            except Exception as exc:
                return f"I couldn't read my memories: {exc}"
            if not memories:
                return "Nothing saved yet. Tell me something worth remembering, or use /remember <fact>."
            return "Here's what I currently remember:\n" + "\n".join(
                f"• [{item['category']}] {item['content']}" for item in memories
            )
        if lowered.startswith("/remember"):
            fact = command[len("/remember"):].strip()
            if not fact:
                return "Use /remember followed by the fact you want me to retain."
            try:
                self.memory.remember_explicit(fact)
                return "Saved to long-term memory. You can inspect it with /memories."
            except Exception as exc:
                return f"I couldn't save that memory: {exc}"
        if lowered.startswith("/forget"):
            phrase = command[len("/forget"):].strip()
            if not phrase:
                return "Use /forget followed by a phrase to find memories to delete."
            return self._forget_memory_phrase(phrase)
        return "I don't recognise that command. Type /help to see the available commands."

    def _forget_memory_phrase(self, phrase: str) -> str:
        if not phrase:
            return "Tell me what you want me to forget."
        try:
            count = self.memory.forget(phrase)
            return f"Forgot {count} matching memory entr{'y' if count == 1 else 'ies'}."
        except Exception as exc:
            return f"I couldn't update memory: {exc}"

    def _show_local_reply(self, reply: str) -> None:
        if self.state_machine.is_state("SPEAKING"):
            self.state_machine.change_state("IDLE")
        if self.state_machine.is_state("THINKING"):
            self.state_machine.change_state("IDLE")
        if self.state_machine.is_state("IDLE"):
            self.state_machine.change_state("LISTENING")
            self.state_machine.change_state("THINKING")
            self.state_machine.change_state("SPEAKING")
        elif self.state_machine.is_state("SLEEPING") and reply == "I'm back.":
            self.state_machine.change_state("IDLE")
            self.state_machine.change_state("LISTENING")
            self.state_machine.change_state("THINKING")
            self.state_machine.change_state("SPEAKING")
        self.refresh_state()
        self.show_assistant_subtitle(reply)
        self.history.append(f"<b>Tuna</b> · {self._escape(reply).replace(chr(10), '<br>')}")
        QTimer.singleShot(1100, self._finish_speaking)
        self.history.verticalScrollBar().setValue(
            self.history.verticalScrollBar().maximum()
        )

    def _on_chat_success(self, reply: str) -> None:
        if self.state_machine.is_state("THINKING"):
            self.state_machine.change_state("SPEAKING")
        self.refresh_state()
        self.show_assistant_subtitle(reply)
        self.history.append(f"<b>Tuna</b> · {self._escape(reply).replace(chr(10), '<br>')}")
        QTimer.singleShot(1100, self._finish_speaking)
        self.history.verticalScrollBar().setValue(
            self.history.verticalScrollBar().maximum()
        )

    def _on_chat_failure(self, error: str) -> None:
        if self.state_machine.is_state("THINKING"):
            self.state_machine.change_state("ERROR")
        self.refresh_state()
        message = f"I couldn't complete that turn. {error}"
        self.show_assistant_subtitle(message)
        self.history.append(f"<b>System</b> · {self._escape(message)}")
        QTimer.singleShot(1600, self._recover_from_error)

    def _recover_from_error(self) -> None:
        if self.state_machine.is_state("ERROR"):
            self.state_machine.change_state("BOOTING")
            self.state_machine.change_state("IDLE")
            self.refresh_state()

    def _on_worker_finished(self) -> None:
        self.input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self.input.setFocus() if self._expanded else None
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

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
