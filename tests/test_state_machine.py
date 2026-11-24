import unittest

from app.core.state_machine import (
    InvalidStateError,
    InvalidTransitionError,
    StateMachine,
)


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = StateMachine()

    def test_starts_in_booting(self) -> None:
        self.assertEqual(self.machine.current_state, "BOOTING")

    def test_valid_path(self) -> None:
        for state in ("IDLE", "LISTENING", "THINKING", "SPEAKING", "IDLE"):
            self.machine.change_state(state)
        self.assertEqual(self.machine.current_state, "IDLE")

    def test_invalid_transition_does_not_change_state(self) -> None:
        self.machine.change_state("IDLE")
        self.machine.change_state("LISTENING")
        with self.assertRaises(InvalidTransitionError):
            self.machine.change_state("SPEAKING")
        self.assertEqual(self.machine.current_state, "LISTENING")

    def test_unknown_state_is_rejected(self) -> None:
        with self.assertRaises(InvalidStateError):
            self.machine.change_state("DANCING")
        self.assertEqual(self.machine.current_state, "BOOTING")

    def test_sleep_and_wake_path(self) -> None:
        self.machine.change_state("IDLE")
        self.machine.change_state("SLEEPING")
        self.machine.change_state("IDLE")
        self.assertEqual(self.machine.current_state, "IDLE")


if __name__ == "__main__":
    unittest.main()
