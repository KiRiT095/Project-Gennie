"""Short-lived conversation context, independent of the model provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Conversation:
    conversation_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    max_history_messages: int = 16

    def __post_init__(self) -> None:
        self.messages = [
            {"role": item["role"], "content": item["content"]}
            for item in self.messages
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ][-self.max_history_messages :]

    def add(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        cleaned = content.strip()
        if not cleaned:
            return
        self.messages.append({"role": role, "content": cleaned})
        self.messages = self.messages[-self.max_history_messages :]

    def prompt_messages(self, system_prompt: str) -> list[dict[str, str]]:
        return [{"role": "system", "content": system_prompt}, *self.messages]

    def transcript(self) -> tuple[dict[str, str], ...]:
        return tuple(dict(message) for message in self.messages)
