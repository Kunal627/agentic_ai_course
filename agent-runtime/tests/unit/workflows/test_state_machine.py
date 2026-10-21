
import pytest

from agent_runtime.workflows.models import (
    WorkflowDefinition,
    WorkflowTransition,
)
from agent_runtime.workflows.state_machine import (
    InvalidWorkflowTransitionError,
    WorkflowStateMachine,
)


@pytest.fixture
def machine() -> WorkflowStateMachine:
    definition = WorkflowDefinition(
        name="sample_workflow",
        version="1.0.0",
        initial_state="VALIDATE",
        states=frozenset({
            "VALIDATE",
            "PROCESS",
            "COMPLETE",
        }),
        transitions=(
            WorkflowTransition(
                source="VALIDATE",
                event="input_validated",
                target="PROCESS",
            ),
            WorkflowTransition(
                source="PROCESS",
                event="processing_succeeded",
                target="COMPLETE",
            ),
        ),
    )
    return WorkflowStateMachine(definition)


def test_create_run_starts_in_initial_state(machine):
    run = machine.create_run()

    assert run.current_state == "VALIDATE"
    assert run.status == "pending"
    assert run.transition_history == []


def test_start_and_apply_valid_transition(machine):
    run = machine.create_run()
    machine.start(run)

    target = machine.transition(run, "input_validated")

    assert target == "PROCESS"
    assert run.current_state == "PROCESS"
    assert run.status == "running"
    assert len(run.transition_history) == 1

    record = run.transition_history[0]
    assert record.source == "VALIDATE"
    assert record.event == "input_validated"
    assert record.target == "PROCESS"


def test_rejects_undefined_transition(machine):
    run = machine.create_run()
    machine.start(run)

    with pytest.raises(
        InvalidWorkflowTransitionError,
        match="not permitted",
    ):
        machine.transition(run, "processing_succeeded")

    assert run.current_state == "VALIDATE"
    assert run.transition_history == []


def test_rejects_transition_before_start(machine):
    run = machine.create_run()

    with pytest.raises(
        InvalidWorkflowTransitionError,
        match="pending",
    ):
        machine.transition(run, "input_validated")


def test_rejects_starting_twice(machine):
    run = machine.create_run()
    machine.start(run)

    with pytest.raises(
        InvalidWorkflowTransitionError,
        match="running",
    ):
        machine.start(run)


def test_complete_workflow(machine):
    run = machine.create_run()
    machine.start(run)
    machine.transition(run, "input_validated")
    machine.transition(run, "processing_succeeded")
    machine.complete(run)

    assert run.current_state == "COMPLETE"
    assert run.status == "completed"
    assert run.completed_at is not None
    assert len(run.transition_history) == 2


def test_rejects_transition_after_completion(machine):
    run = machine.create_run()
    machine.start(run)
    machine.transition(run, "input_validated")
    machine.transition(run, "processing_succeeded")
    machine.complete(run)

    with pytest.raises(
        InvalidWorkflowTransitionError,
        match="completed",
    ):
        machine.transition(run, "anything")

    assert len(run.transition_history) == 2


def test_fail_workflow(machine):
    run = machine.create_run()
    machine.start(run)
    machine.fail(run, "Simulated failure")

    assert run.status == "failed"
    assert run.error == "Simulated failure"
    assert run.completed_at is not None


def test_cancel_workflow(machine):
    run = machine.create_run()
    machine.start(run)
    machine.cancel(run, "Cancelled by caller")

    assert run.status == "cancelled"
    assert run.error == "Cancelled by caller"
    assert run.completed_at is not None
