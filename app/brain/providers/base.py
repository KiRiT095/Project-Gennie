"""Provider contract used by Gennie's reasoning layer."""

from __future__ import annotations

from typing import Protocol, Sequence, Mapping, Any


class ChatProvider(Protocol):
    def chat(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        response_format: str | dict[str, Any] | None = None,
    ) -> str:
        """Return the assistant's user-facing response."""
