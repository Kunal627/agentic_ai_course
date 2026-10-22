
import pytest

from src.workflow_poc.models  import WorkflowStatus
from src.workflow_poc.state_machine import (
    InvalidTransitionError,
    transition,
    validate_transition,
)


def test_normal_transition_is_allowed():
    result = transition(
        WorkflowStatus.RECEIVED,
        WorkflowStatus.VALIDATING,
    )

    assert result == WorkflowStatus.VALIDATING


def test_transition_to_completed_after_policy_check_is_allowed():
    validate_transition(
        WorkflowStatus.POLICY_CHECK,
        WorkflowStatus.COMPLETED,
    )


def test_policy_check_can_require_human_approval():
    validate_transition(
        WorkflowStatus.POLICY_CHECK,
        WorkflowStatus.AWAITING_APPROVAL,
    )


def test_human_approval_can_complete_workflow():
    validate_transition(
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.COMPLETED,
    )


def test_human_rejection_is_allowed():
    validate_transition(
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.REJECTED,
    )


def test_cannot_skip_directly_to_completed():
    with pytest.raises(InvalidTransitionError):
        transition(
            WorkflowStatus.RECEIVED,
            WorkflowStatus.COMPLETED,
        )


def test_terminal_state_cannot_transition():
    with pytest.raises(InvalidTransitionError):
        transition(
            WorkflowStatus.COMPLETED,
            WorkflowStatus.VALIDATING,
        )


def test_active_workflow_can_fail():
    validate_transition(
        WorkflowStatus.AI_REVIEW,
        WorkflowStatus.FAILED,
    )
