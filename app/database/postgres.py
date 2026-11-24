"""PostgreSQL persistence for conversations and selective memories."""

from __future__ import annotations

import os
import re
from typing import Any


class DatabaseUnavailable(RuntimeError):
    """Raised when PostgreSQL cannot be reached or psycopg is missing."""


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tuna_conversations (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tuna_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES tuna_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS tuna_messages_conversation_idx
    ON tuna_messages (conversation_id, id);

CREATE TABLE IF NOT EXISTS tuna_memories (
    id BIGSERIAL PRIMARY KEY,
    memory_key TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('core', 'long_term', 'project', 'episodic')),
    content TEXT NOT NULL,
    importance SMALLINT NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    confidence REAL NOT NULL DEFAULT 0.85 CHECK (confidence BETWEEN 0 AND 1),
    source TEXT NOT NULL DEFAULT 'conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS tuna_memories_category_importance_idx
    ON tuna_memories (category, importance DESC);
CREATE INDEX IF NOT EXISTS tuna_memories_search_idx
    ON tuna_memories USING GIN (to_tsvector('simple', content));
"""


class PostgresStore:
    def __init__(self, dsn: str | None = None, connect_timeout: int = 2) -> None:
        self.dsn = dsn or os.getenv("TUNA_DATABASE_URL", "postgresql:///tuna")
        self.connect_timeout = connect_timeout
        self.available = False
        self.last_error = "PostgreSQL has not been checked yet."

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise DatabaseUnavailable(
                "Psycopg is not installed. Run: python -m pip install -e ."
            ) from exc
        try:
            return psycopg.connect(self.dsn, connect_timeout=self.connect_timeout)
        except Exception as exc:
            # Never echo the connection URL: it may contain a password.
            raise DatabaseUnavailable(
                "PostgreSQL connection failed. Check that the server is running "
                "and TUNA_DATABASE_URL points to the Tuna database."
            ) from exc

    def initialize(self) -> bool:
        try:
            with self._connect() as connection:
                # Execute statements individually so Psycopg does not try to
                # prepare a multi-statement SQL string as one server command.
                for statement in SCHEMA_SQL.split(";"):
                    if statement.strip():
                        connection.execute(statement)
            self.available = True
            self.last_error = ""
            return True
        except Exception as exc:
            self.mark_unavailable(str(exc))
            return False

    def mark_unavailable(self, reason: str) -> None:
        self.available = False
        self.last_error = reason

    def latest_or_create_conversation(self, conversation_id: str) -> tuple[str, list[dict[str, str]]]:
        """Resume the most recently updated conversation, or create a new one."""
        if not self.available:
            return conversation_id, []
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT id::text FROM tuna_conversations ORDER BY updated_at DESC LIMIT 1"
                ).fetchone()
                if row:
                    selected_id = row[0]
                else:
                    connection.execute(
                        "INSERT INTO tuna_conversations (id) VALUES (%s)", (conversation_id,)
                    )
                    selected_id = conversation_id
                rows = connection.execute(
                    "SELECT role, content FROM ("
                    " SELECT role, content, id FROM tuna_messages"
                    " WHERE conversation_id = %s::uuid ORDER BY id DESC LIMIT 16"
                    ") recent ORDER BY id ASC",
                    (selected_id,),
                ).fetchall()
                return selected_id, [{"role": role, "content": content} for role, content in rows]
        except Exception as exc:
            self.mark_unavailable(str(exc))
            return conversation_id, []

    def create_conversation(self, conversation_id: str) -> None:
        if not self.available:
            return
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO tuna_conversations (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
                    (conversation_id,),
                )
        except Exception as exc:
            self.mark_unavailable("Could not create a new conversation in PostgreSQL.")
            raise DatabaseUnavailable(self.last_error) from exc

    def save_exchange(self, conversation_id: str, user_message: str, assistant_message: str) -> None:
        if not self.available:
            return
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO tuna_conversations (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
                    (conversation_id,),
                )
                connection.execute(
                    "INSERT INTO tuna_messages (conversation_id, role, content) VALUES (%s, 'user', %s), (%s, 'assistant', %s)",
                    (conversation_id, user_message, conversation_id, assistant_message),
                )
                connection.execute(
                    "UPDATE tuna_conversations SET updated_at = NOW() WHERE id = %s",
                    (conversation_id,),
                )
        except Exception as exc:
            self.mark_unavailable(str(exc))
            raise DatabaseUnavailable("Could not persist the conversation.") from exc

    @staticmethod
    def _build_search_query(query: str) -> str:
        """Build a safe OR-style tsquery from meaningful words in the user turn."""
        stop_words = {
            "what", "who", "where", "when", "why", "how", "tell", "show",
            "please", "about", "with", "from", "that", "this", "have",
            "does", "did", "are", "was", "were", "the", "and", "for",
            "you", "your", "my", "me", "can", "could", "would", "should",
            "is", "am", "a", "an", "i", "it", "to", "of", "on", "in",
        }
        tokens = [
            token for token in re.findall(r"[a-zA-Z0-9_]+", query.casefold())
            if len(token) > 1 and token not in stop_words
        ]
        return " | ".join(f"{token}:*" for token in dict.fromkeys(tokens[:12]))

    def retrieve_memories(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        if not self.available:
            return []
        try:
            ts_query = self._build_search_query(query)
            with self._connect() as connection:
                if ts_query:
                    rows = connection.execute(
                        "SELECT id, category, content, importance, confidence "
                        "FROM tuna_memories "
                        "WHERE category = 'core' OR to_tsvector('simple', content) @@ to_tsquery('simple', %s) "
                        "ORDER BY (category = 'core') DESC, "
                        "ts_rank(to_tsvector('simple', content), to_tsquery('simple', %s)) DESC, "
                        "importance DESC, updated_at DESC LIMIT %s",
                        (ts_query, ts_query, limit),
                    ).fetchall()
                else:
                    rows = connection.execute(
                        "SELECT id, category, content, importance, confidence "
                        "FROM tuna_memories WHERE category = 'core' "
                        "ORDER BY importance DESC, updated_at DESC LIMIT %s",
                        (limit,),
                    ).fetchall()
                if rows:
                    ids = [row[0] for row in rows]
                    connection.execute(
                        "UPDATE tuna_memories SET last_accessed_at = NOW() WHERE id = ANY(%s)",
                        (ids,),
                    )
                return [
                    {"id": row[0], "category": row[1], "content": row[2],
                     "importance": row[3], "confidence": row[4]}
                    for row in rows
                ]
        except Exception as exc:
            self.mark_unavailable(str(exc))
            return []

    def upsert_memory(
        self, memory_key: str, category: str, content: str,
        importance: int = 3, confidence: float = 0.85, source: str = "conversation",
    ) -> None:
        if not self.available:
            raise DatabaseUnavailable("Memory storage is unavailable.")
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO tuna_memories "
                    "(memory_key, category, content, importance, confidence, source) "
                    "VALUES (%s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (memory_key) DO UPDATE SET "
                    "category = EXCLUDED.category, content = EXCLUDED.content, "
                    "importance = EXCLUDED.importance, confidence = EXCLUDED.confidence, "
                    "source = EXCLUDED.source, updated_at = NOW()",
                    (memory_key, category, content, importance, confidence, source),
                )
        except Exception as exc:
            self.mark_unavailable("Could not write to the Tuna memory database.")
            raise DatabaseUnavailable(self.last_error) from exc

    def list_memories(self, limit: int = 30) -> list[dict[str, Any]]:
        if not self.available:
            return []
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT id, category, content, importance, confidence, updated_at "
                    "FROM tuna_memories ORDER BY importance DESC, updated_at DESC LIMIT %s",
                    (limit,),
                ).fetchall()
        except Exception as exc:
            self.mark_unavailable("Could not read from the Tuna memory database.")
            raise DatabaseUnavailable(self.last_error) from exc
        return [
            {"id": row[0], "category": row[1], "content": row[2],
             "importance": row[3], "confidence": row[4], "updated_at": row[5]}
            for row in rows
        ]

    def forget_memories(self, phrase: str) -> int:
        if not self.available:
            raise DatabaseUnavailable("Memory storage is unavailable.")
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM tuna_memories WHERE content ILIKE %s OR memory_key ILIKE %s",
                    (f"%{phrase}%", f"%{phrase}%"),
                )
                return cursor.rowcount
        except Exception as exc:
            self.mark_unavailable("Could not delete from the Tuna memory database.")
            raise DatabaseUnavailable(self.last_error) from exc
