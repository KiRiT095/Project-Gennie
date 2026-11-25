"""Coordinates Gennie's high-level startup lifecycle."""

from app.core.state_machine import StateMachine


class Lifecycle:
    def __init__(self, state_machine: StateMachine) -> None:
        self.state_machine = state_machine

    def start(self) -> None:
        if not self.state_machine.is_state("BOOTING"):
            raise RuntimeError("Lifecycle.start() can only run from BOOTING.")
        # Future startup checks (configuration, assets, services) belong here.
        self.state_machine.change_state("IDLE")
