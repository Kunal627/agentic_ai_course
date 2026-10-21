
import pytest
from pydantic import ValidationError

from agent_runtime.workflows.models import (
    WorkflowDefinition,
    WorkflowTransition,
    WorkflowRun,
)


def make_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
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


def test_valid_workflow_definition():
    definition = make_definition()

    assert definition.initial_state == "VALIDATE"
    assert len(definition.transitions) == 2


def test_rejects_unknown_initial_state():
    with pytest.raises(ValidationError):
        WorkflowDefinition(
            name="invalid",
            version="1.0.0",
            initial_state="MISSING",
            states=frozenset({"VALIDATE"}),
        )


def test_rejects_unknown_transition_target():
    with pytest.raises(ValidationError):
        WorkflowDefinition(
            name="invalid",
            version="1.0.0",
            initial_state="VALIDATE",
            states=frozenset({"VALIDATE"}),
            transitions=(
                WorkflowTransition(
                    source="VALIDATE",
                    event="continue",
                    target="MISSING",
                ),
            ),
        )


def test_rejects_duplicate_transition_event():
    transition = WorkflowTransition(
        source="VALIDATE",
        event="continue",
        target="PROCESS",
    )

    with pytest.raises(ValidationError, match="Duplicate transition"):
        WorkflowDefinition(
            name="invalid",
            version="1.0.0",
            initial_state="VALIDATE",
            states=frozenset({"VALIDATE", "PROCESS"}),
            transitions=(transition, transition),
        )


def test_workflow_run_has_independent_context_and_history():
    first = WorkflowRun(
        workflow_name="sample_workflow",
        workflow_version="1.0.0",
        current_state="VALIDATE",
    )
    second = WorkflowRun(
        workflow_name="sample_workflow",
        workflow_version="1.0.0",
        current_state="VALIDATE",
    )

    first.context["input"] = "example"

    assert first.run_id != second.run_id
    assert second.context == {}
    assert first.transition_history == []
