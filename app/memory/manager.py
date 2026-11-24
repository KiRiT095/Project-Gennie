"""User-controlled memory operations and background extraction."""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import Future, ThreadPoolExecutor

from app.brain.providers.base import ChatProvider
from app.database.postgres import PostgresStore
from app.memory.extractor import MemoryExtractor, extract_obvious_memory, looks_like_memory_candidate


class MemoryManager:
    def __init__(self, store: PostgresStore, provider: ChatProvider) -> None:
        self.store = store
        self.extractor = MemoryExtractor(provider)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tuna-memory")
        self._pending: set[Future] = set()

    def schedule_extraction(self, user_message: str) -> None:
        if not self.store.available or not looks_like_memory_candidate(user_message):
            return
        # A few unmistakable statements (name, explicit preference, stated
        # project/decision) can be stored immediately and accurately without
        # asking a 4B model to perform a second inference pass.
        obvious = extract_obvious_memory(user_message)
        if obvious:
            try:
                for item in obvious:
                    self.store.upsert_memory(
                        memory_key=item["key"], category=item["category"],
                        content=item["content"], importance=item["importance"],
                        confidence=item["confidence"], source="direct-extraction",
                    )
            except Exception:
                return
            return
        future = self._executor.submit(self._extract_and_save, user_message)
        self._pending.add(future)
        future.add_done_callback(self._pending.discard)

    def _extract_and_save(self, user_message: str) -> None:
        try:
            memories = self.extractor.extract(user_message)
            for item in memories:
                self.store.upsert_memory(
                    memory_key=item["key"], category=item["category"],
                    content=item["content"], importance=item["importance"],
                    confidence=item["confidence"], source="conversation",
                )
        except Exception:
            # Memory extraction must never break the conversation.
            return

    def remember_explicit(self, content: str) -> None:
        """Save an explicit user request without relying on model inference."""
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("Tell me what to remember.")
        if re.search(
            r"(?i)(password|api[_ -]?key|access token|secret key|private key|credit card|cvv|one[- ]time password|otp)",
            cleaned,
        ):
            raise ValueError("I won't store passwords, authentication secrets or payment credentials.")
        normalised = re.sub(r"\s+", " ", cleaned).casefold()
        key = "explicit-" + hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:24]
        self.store.upsert_memory(
            memory_key=key, category="long_term", content=cleaned,
            importance=4, confidence=1.0, source="explicit-user-request",
        )

    def list_memories(self) -> list[dict]:
        return self.store.list_memories()

    def forget(self, phrase: str) -> int:
        return self.store.forget_memories(phrase.strip())

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
