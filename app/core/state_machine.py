"""Small, dependency-free state machine for Tuna's lifecycle."""

from typing import Final


class InvalidStateError(ValueError):
    """Raised when a state name is not recognised."""


class InvalidTransitionError(ValueError):
    """Raised when a transition is not allowed."""


class StateMachine:
    STATES: Final[frozenset[str]] = frozenset(
        {
            "BOOTING",
            "IDLE",
            "LISTENING",
            "THINKING",
            "SPEAKING",
            "SLEEPING",
            "ERROR",
        }
    )

    TRANSITIONS: Final[dict[str, frozenset[str]]] = {
        "BOOTING": frozenset({"IDLE", "ERROR"}),
        "IDLE": frozenset({"LISTENING", "SLEEPING", "ERROR"}),
        "LISTENING": frozenset({"THINKING", "IDLE", "ERROR"}),
        "THINKING": frozenset({"SPEAKING", "IDLE", "ERROR"}),
        "SPEAKING": frozenset({"IDLE", "ERROR"}),
        "SLEEPING": frozenset({"IDLE", "ERROR"}),
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
            raise InvalidTransitionError(
                f"Transition {self._current_state} -> {next_state} is not allowed."
            )

        previous_state = self._current_state
        self._current_state = next_state
        return previous_state

    @classmethod
    def _validate_state_name(cls, state: str) -> None:
        if state not in cls.STATES:
            raise InvalidStateError(f"Unknown Tuna state: {state!r}")
