
from .models import WorkflowStatus


class InvalidTransitionError(ValueError):
    """Raised when a workflow attempts an illegal state transition."""


ALLOWED_TRANSITIONS: dict[WorkflowStatus, frozenset[WorkflowStatus]] = {
    WorkflowStatus.RECEIVED: frozenset({
        WorkflowStatus.VALIDATING,
        WorkflowStatus.FAILED,
    }),
    WorkflowStatus.VALIDATING: frozenset({
        WorkflowStatus.AI_REVIEW,
        WorkflowStatus.FAILED,
    }),
    WorkflowStatus.AI_REVIEW: frozenset({
        WorkflowStatus.POLICY_CHECK,
        WorkflowStatus.FAILED,
    }),
    WorkflowStatus.POLICY_CHECK: frozenset({
        WorkflowStatus.COMPLETED,
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.FAILED,
    }),
    WorkflowStatus.AWAITING_APPROVAL: frozenset({
        WorkflowStatus.COMPLETED,
        WorkflowStatus.REJECTED,
        WorkflowStatus.FAILED,
    }),
    WorkflowStatus.COMPLETED: frozenset(),
    WorkflowStatus.REJECTED: frozenset(),
    WorkflowStatus.FAILED: frozenset(),
}


def validate_transition(
    current: WorkflowStatus,
    target: WorkflowStatus,
) -> None:
    """Raise InvalidTransitionError if the transition is not allowed."""

    allowed = ALLOWED_TRANSITIONS[current]

    if target not in allowed:
        raise InvalidTransitionError(
            f"Transition from '{current.value}' "
            f"to '{target.value}' is not allowed."
        )


def transition(
    current: WorkflowStatus,
    target: WorkflowStatus,
) -> WorkflowStatus:
    """Validate a transition and return the resulting state."""

    validate_transition(current, target)
    return target
