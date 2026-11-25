import pytest
from app.core.state_machine import InvalidStateError, InvalidTransitionError, StateMachine

def test_valid_summon_and_return_cycle():
    machine = StateMachine()
    machine.change_state("IDLE")
    machine.change_state("SLEEPING")
    machine.change_state("EMERGING")
    machine.change_state("LISTENING")
    machine.change_state("THINKING")
    machine.change_state("SPEAKING")
    machine.change_state("IDLE")
    machine.change_state("RETURNING")
    machine.change_state("SLEEPING")
    assert machine.current_state == "SLEEPING"

def test_invalid_transition_does_not_change_state():
    machine = StateMachine()
    machine.change_state("IDLE")
    machine.change_state("LISTENING")
    with pytest.raises(InvalidTransitionError):
        machine.change_state("SPEAKING")
    assert machine.current_state == "LISTENING"

def test_unknown_state_is_rejected():
    machine = StateMachine()
    with pytest.raises(InvalidStateError):
        machine.change_state("MAGIC")
