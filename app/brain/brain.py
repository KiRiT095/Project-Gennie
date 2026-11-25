"""Orchestrates personality, retrieved memories, conversation and inference."""

from __future__ import annotations

from pathlib import Path
import re

from app.brain.conversation import Conversation
from app.brain.providers.base import ChatProvider
from app.database.postgres import PostgresStore


class GennieBrain:
    def __init__(
        self,
        provider: ChatProvider,
        conversation: Conversation,
        store: PostgresStore,
        personality_path: Path | None = None,
    ) -> None:
        self.provider = provider
        self.conversation = conversation
        self.store = store
        self.personality_path = personality_path or (
            Path(__file__).resolve().parent / "prompts" / "system_prompt.txt"
        )
        self.personality = self.personality_path.read_text(encoding="utf-8")

    def respond(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("A message cannot be empty.")

        memory_context = ""
        if self.store.available:
            try:
                lowered = user_message.casefold()
                asks_about_memory = (
                    ("remember" in lowered or "know" in lowered)
                    and ("about me" in lowered or "about myself" in lowered or "myself" in lowered)
                )
                memories = (
                    self.store.list_memories(limit=12)
                    if asks_about_memory
                    else self.store.retrieve_memories(user_message, limit=6)
                )
                if memories:
                    memory_context = "\n\nRELEVANT LONG-TERM MEMORIES\n" + "\n".join(
                        f"- [{item['category']}] {item['content']}" for item in memories
                    )
            except Exception:
                # A memory outage must not prevent ordinary conversation.
                memory_context = ""

        system_message = self.personality.strip() + memory_context
        self.conversation.add("user", user_message)
        try:
            reply = self.provider.chat(self.conversation.prompt_messages(system_message))
        except Exception:
            # Keep the in-memory transcript intact so a retry retains context.
            raise
        # Enforce the requested no-emoji voice/style even if the local model
        # ignores the system instruction. Keep stored history consistent with
        # what the UI and TTS actually deliver.
        reply = re.sub(
            r"[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]",
            "",
            reply,
        )
        reply = re.sub(r"[ \t]{2,}", " ", reply)
        reply = re.sub(r"\s+([.,!?;:])", r"\1", reply).strip()
        if not reply:
            reply = "I'm here. What would you like to talk about?"
        self.conversation.add("assistant", reply)

        if self.store.available:
            try:
                self.store.save_exchange(
                    self.conversation.conversation_id, user_message, reply
                )
            except Exception:
                # Database errors are surfaced in the app's memory status;
                # the current chat remains usable for this session.
                self.store.mark_unavailable("Could not save this conversation to PostgreSQL.")
        return reply


# Backwards-compatible import alias for existing scripts and tests.
TunaBrain = GennieBrain
