
from datetime import datetime, timezone

from agent_runtime.workflows.models import (
    WorkflowDefinition,
    WorkflowRun,
    WorkflowTransitionRecord,
)


class InvalidWorkflowTransitionError(Exception):
    """Raised when a workflow transition is not permitted."""


class WorkflowStateMachine:
    """Validates and applies explicit workflow state transitions."""

    TERMINAL_STATUSES = frozenset({
        "completed",
        "failed",
        "cancelled",
    })

    def __init__(self, definition: WorkflowDefinition) -> None:
        self.definition = definition

        # Index transitions for deterministic lookup.
        self._transitions = {
            (transition.source, transition.event): transition
            for transition in definition.transitions
        }

    def create_run(self) -> WorkflowRun:
        """Create a new workflow run in its initial state."""
        return WorkflowRun(
            workflow_name=self.definition.name,
            workflow_version=self.definition.version,
            current_state=self.definition.initial_state,
        )

    def start(self, run: WorkflowRun) -> None:
        """Move a pending workflow run into execution."""
        self._validate_run(run)

        if run.status != "pending":
            raise InvalidWorkflowTransitionError(
                f"Cannot start workflow in '{run.status}' status."
            )

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)

    def transition(self, run: WorkflowRun, event: str) -> str:
        """Apply an explicitly declared transition and return its target."""
        self._validate_run(run)

        if run.status != "running":
            raise InvalidWorkflowTransitionError(
                f"Cannot transition workflow in '{run.status}' status."
            )

        transition = self._transitions.get(
            (run.current_state, event)
        )

        if transition is None:
            raise InvalidWorkflowTransitionError(
                f"Event '{event}' is not permitted from state "
                f"'{run.current_state}'."
            )

        source = run.current_state
        target = transition.target

        # Record only successfully applied transitions.
        run.transition_history.append(
            WorkflowTransitionRecord(
                source=source,
                event=event,
                target=target,
            )
        )
        run.current_state = target

        return target

    def complete(self, run: WorkflowRun) -> None:
        """Mark a running workflow as completed."""
        self._validate_run(run)

        if run.status != "running":
            raise InvalidWorkflowTransitionError(
                f"Cannot complete workflow in '{run.status}' status."
            )

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)

    def fail(self, run: WorkflowRun, error: str) -> None:
        """Mark a running workflow as failed."""
        self._validate_run(run)

        if run.status != "running":
            raise InvalidWorkflowTransitionError(
                f"Cannot fail workflow in '{run.status}' status."
            )

        run.status = "failed"
        run.error = error
        run.completed_at = datetime.now(timezone.utc)

    def cancel(
        self,
        run: WorkflowRun,
        reason: str = "Workflow cancelled.",
    ) -> None:
        """Cancel a pending or running workflow."""
        self._validate_run(run)

        if run.status not in {"pending", "running"}:
            raise InvalidWorkflowTransitionError(
                f"Cannot cancel workflow in '{run.status}' status."
            )

        run.status = "cancelled"
        run.error = reason
        run.completed_at = datetime.now(timezone.utc)

    def _validate_run(self, run: WorkflowRun) -> None:
        """Ensure the run belongs to this workflow definition."""
        if run.workflow_name != self.definition.name:
            raise ValueError(
                "Workflow run name does not match this definition."
            )

        if run.workflow_version != self.definition.version:
            raise ValueError(
                "Workflow run version does not match this definition."
            )

        if run.current_state not in self.definition.states:
            raise ValueError(
                f"Unknown current workflow state: {run.current_state}"
            )
