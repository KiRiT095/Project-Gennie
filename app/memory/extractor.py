"""Conservative, LLM-assisted memory extraction."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.brain.providers.base import ChatProvider


EXTRACTION_SYSTEM = """You are Gennie's memory curator. Analyse ONLY the user's supplied message.
Return JSON with exactly this shape: {\"decision\":\"save\" or \"ignore\", \"memories\":[{\"key\":string,\"category\":\"core\"|\"long_term\"|\"project\"|\"episodic\",\"content\":string,\"importance\":1-5,\"confidence\":0-1}]}.
Save only durable, useful facts about the user, their preferences, ongoing projects, explicit decisions, or lessons that will help future conversations. Ignore greetings, jokes, hypotheticals, one-off questions, temporary details and facts merely suggested by the assistant. Never infer facts. Do not save passwords, API keys, tokens, private keys, payment credentials, or highly sensitive personal information. Prefer updating a stable key when the new fact corrects an older one. Keep each memory concise, self-contained and factual. If nothing qualifies, return decision=ignore and an empty memories array.
"""

CANDIDATE_MARKERS = (
    "remember", "my name is", "call me", "i prefer", "i like", "i dislike",
    "i hate", "i'm building", "i am building", "my project", "i decided",
    "i've decided", "i have decided", "my goal", "i study", "i'm studying",
    "i am studying", "i work", "i use", "i'm using", "i am using",
    "i live", "i moved", "i'm a ", "i am a ", "i'm an ", "i am an ",
    "my setup", "my device", "my course", "my degree", "i own", "i have a ",
    "i no longer", "i changed", "actually,", "from now on", "don't remember", "do not remember",
)


def looks_like_memory_candidate(message: str) -> bool:
    lowered = message.casefold()
    if re.search(r"\b(don't|do not|never)\s+remember\b", lowered):
        return False
    return any(marker in lowered for marker in CANDIDATE_MARKERS)


def extract_obvious_memory(message: str) -> list[dict[str, Any]]:
    """Extract a few high-confidence, explicitly phrased facts without another model call."""
    patterns = (
        (r"\bmy name is ([^.!?,;]+)", "user_name", "core", 5, "The user's name is {value}."),
        (r"\bcall me ([^.!?,;]+)", "user_name", "core", 5, "The user prefers to be called {value}."),
        (r"\bi prefer ([^.!?;]+)", "user_preference", "core", 4, "The user prefers {value}."),
        (r"\bi dislike ([^.!?;]+)", "user_preference_dislike", "core", 3, "The user dislikes {value}."),
        (r"\bi am building ([^.!?;]+)", "current_project", "project", 4, "The user is building {value}."),
        (r"\bi'm building ([^.!?;]+)", "current_project", "project", 4, "The user is building {value}."),
        (r"\bmy goal is ([^.!?;]+)", "user_goal", "long_term", 4, "The user's goal is {value}."),
        (r"\bi decided to ([^.!?;]+)", "user_decision", "long_term", 4, "The user decided to {value}."),
        (r"\bi have decided to ([^.!?;]+)", "user_decision", "long_term", 4, "The user decided to {value}."),
    )
    for pattern, key, category, importance, template in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip(" .,!?")
            if not value or re.search(r"(?i)(password|api[_ -]?key|access token|private key|credit card)", value):
                return []
            stable_key = key if key == "user_name" else (
                key + ":" + hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()[:10]
            )
            return [{
                "key": stable_key,
                "category": category,
                "content": template.format(value=value),
                "importance": importance,
                "confidence": 0.99,
            }]
    return []


def parse_memory_payload(raw: str) -> list[dict[str, Any]]:
    """Validate the extractor's JSON before allowing it to reach the database."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return []
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if not isinstance(payload, dict) or payload.get("decision") != "save":
        return []
    items = payload.get("memories", [])
    if not isinstance(items, list):
        return []

    valid: list[dict[str, Any]] = []
    allowed_categories = {"core", "long_term", "project", "episodic"}
    for item in items[:3]:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip().casefold()[:120]
        category = str(item.get("category", "long_term")).strip()
        content = str(item.get("content", "")).strip()[:700]
        try:
            importance = int(item.get("importance", 3))
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            continue
        if (not key or not content or category not in allowed_categories
                or not 1 <= importance <= 5 or not 0.75 <= confidence <= 1.0):
            continue
        if re.search(r"(?i)(password|api[_ -]?key|access token|private key|credit card)", content):
            continue
        valid.append({
            "key": key, "category": category, "content": content,
            "importance": importance, "confidence": confidence,
        })
    return valid


class MemoryExtractor:
    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    def extract(self, user_message: str) -> list[dict[str, Any]]:
        if not looks_like_memory_candidate(user_message):
            return []
        raw = self.provider.chat(
            [
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            response_format="json",
        )
        return parse_memory_payload(raw)
