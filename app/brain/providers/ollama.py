"""Ollama adapter using the native local /api/chat endpoint."""

from __future__ import annotations

import json
import os
import re
import threading
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence

from app.brain.providers.base import ChatProvider


class ProviderError(RuntimeError):
    """Raised when the local model cannot produce a response."""


class OllamaProvider(ChatProvider):
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.model = model or os.getenv("GENNIE_MODEL") or os.getenv("TUNA_MODEL", "qwen3:4b-instruct-2507-q4_K_M")
        self.base_url = (base_url or os.getenv("GENNIE_OLLAMA_URL") or os.getenv("TUNA_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout
        # A single local inference at a time is gentler on low-memory devices.
        self._request_lock = threading.Lock()

    def chat(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        response_format: str | dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [dict(item) for item in messages],
            "stream": False,
            # Qwen3 supports this through Ollama's native API. The thinking
            # trace is not conversation content; only message.content is used.
            "think": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.58,
                "num_ctx": 4096,
                "num_predict": 240,
            },
        }
        if response_format is not None:
            payload["format"] = response_format

        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._request_lock:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ProviderError(
                    f"Ollama could not find model {self.model!r}. Run: ollama pull {self.model}"
                ) from exc
            raise ProviderError(f"Ollama returned HTTP {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError(
                "Gennie cannot reach Ollama. Make sure Ollama is running and the model is installed."
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as exc:
            raise ProviderError("Ollama returned an invalid response.") from exc

        if not isinstance(result, dict) or not isinstance(result.get("message"), dict):
            raise ProviderError("Ollama returned an invalid response structure.")
        message = result["message"]
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("The model returned an empty answer.")
        return self._remove_reasoning_leaks(content.strip())

    @staticmethod
    def _remove_reasoning_leaks(text: str) -> str:
        """Defensively remove leaked think blocks; never display hidden traces."""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
        cleaned = cleaned.replace("</think>", "").strip()
        return cleaned or "I lost my train of thought. Try that once more."
