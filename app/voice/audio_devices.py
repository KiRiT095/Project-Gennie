"""Microphone selection shared by wake-word and speech-recognition workers."""

from __future__ import annotations

import os
from typing import Any


BUILT_IN_MIC_HINTS = (
    "macbook air microphone",
    "macbook pro microphone",
    "macbook microphone",
    "built-in microphone",
    "built in microphone",
)


def select_input_device(sounddevice_module: Any, configured: str | None = None) -> int | None:
    """Use an explicit device when configured, otherwise prefer the Mac mic.

    This avoids accidentally selecting a Continuity Camera/iPhone microphone
    when macOS has changed its default input device. The None fallback keeps
    the sounddevice system default on machines without a recognisable built-in
    microphone name.
    """
    raw = (configured if configured is not None else os.getenv("GENNIE_MIC_DEVICE", "")).strip()
    if raw:
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError("GENNIE_MIC_DEVICE must be an integer device index or blank.") from exc

    try:
        devices = sounddevice_module.query_devices()
        for index, device in enumerate(devices):
            name = str(device.get("name", "")).casefold()
            inputs = int(device.get("max_input_channels", 0) or 0)
            if inputs and any(hint in name for hint in BUILT_IN_MIC_HINTS):
                return index
    except Exception:
        return None
    return None
