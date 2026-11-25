"""Validated behavioural states for Project Gennie."""

from typing import Final


class InvalidStateError(ValueError):
    """Raised when a state name is not recognised."""


class InvalidTransitionError(ValueError):
    """Raised when a transition is not allowed."""


class StateMachine:
    STATES: Final[frozenset[str]] = frozenset({
        "BOOTING", "IDLE", "EMERGING", "LISTENING", "THINKING",
        "SPEAKING", "RETURNING", "SLEEPING", "ERROR",
    })
    TRANSITIONS: Final[dict[str, frozenset[str]]] = {
        "BOOTING": frozenset({"IDLE", "ERROR"}),
        "IDLE": frozenset({"EMERGING", "LISTENING", "RETURNING", "SLEEPING", "ERROR"}),
        "EMERGING": frozenset({"LISTENING", "IDLE", "ERROR"}),
        "LISTENING": frozenset({"THINKING", "IDLE", "RETURNING", "ERROR"}),
        "THINKING": frozenset({"SPEAKING", "IDLE", "ERROR"}),
        "SPEAKING": frozenset({"IDLE", "RETURNING", "ERROR"}),
        "RETURNING": frozenset({"SLEEPING", "IDLE", "ERROR"}),
        "SLEEPING": frozenset({"EMERGING", "IDLE", "ERROR"}),
        "ERROR": frozenset({"BOOTING"}),
    }

    def __init__(self) -> None:
        self._current_state = "BOOTING"

    @property
    def current_state(self) -> str:
        return self._current_state

    def get_state(self) -> str:
        return self._current_state

    def is_state(self, requested_state: str) -> bool:
        self._validate_state_name(requested_state)
        return self._current_state == requested_state

    def change_state(self, next_state: str) -> str:
        self._validate_state_name(next_state)
        if next_state not in self.TRANSITIONS[self._current_state]:
            raise InvalidTransitionError(f"Transition {self._current_state} -> {next_state} is not allowed.")
        previous_state = self._current_state
        self._current_state = next_state
        return previous_state

    @classmethod
    def _validate_state_name(cls, state: str) -> None:
        if state not in cls.STATES:
            raise InvalidStateError(f"Unknown Gennie state: {state!r}")
