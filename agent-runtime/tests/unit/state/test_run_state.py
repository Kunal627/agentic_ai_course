
from agent_runtime.state.run_state import RunState
import pytest

def test_new_run_starts_pending() -> None:
    state = RunState()

    assert state.status == "pending"
    assert state.started_at is None
    assert state.completed_at is None


def test_start_does_not_reset_started_at() -> None:
    state = RunState()
    state.start()
    original_started_at = state.started_at

    state.start()

    assert state.started_at == original_started_at

def test_completed_run_cannot_be_overwritten_by_failure() -> None:
    state = RunState()
    state.start()
    state.complete("Success")

    with pytest.raises(ValueError, match="Cannot fail"):
        state.fail("Unexpected error")

    assert state.status == "completed"
    assert state.final_answer == "Success"
    assert state.error is None



def test_cancelled_run_cannot_be_completed() -> None:
    state = RunState()
    state.start()
    state.cancel("Cancelled by user")

    with pytest.raises(ValueError, match="Cannot complete"):
        state.complete("Late response")

    assert state.status == "cancelled"
    assert state.final_answer is None
    assert state.error == "Cancelled by user"

