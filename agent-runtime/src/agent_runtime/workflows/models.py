
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkflowTransition(BaseModel):
    """One explicitly permitted workflow state transition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str = Field(min_length=1)
    event: str = Field(min_length=1)
    target: str = Field(min_length=1)


class WorkflowDefinition(BaseModel):
    """A declarative workflow definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    initial_state: str = Field(min_length=1)
    states: frozenset[str] = Field(min_length=1)
    transitions: tuple[WorkflowTransition, ...] = ()

    @model_validator(mode="after")
    def validate_transitions(self) -> "WorkflowDefinition":
        if self.initial_state not in self.states:
            raise ValueError(
                "initial_state must be included in states"
            )

        seen: set[tuple[str, str]] = set()

        for transition in self.transitions:
            if transition.source not in self.states:
                raise ValueError(
                    f"Unknown transition source: {transition.source}"
                )

            if transition.target not in self.states:
                raise ValueError(
                    f"Unknown transition target: {transition.target}"
                )

            key = (transition.source, transition.event)

            if key in seen:
                raise ValueError(
                    "Duplicate transition for source state "
                    f"'{transition.source}' and event '{transition.event}'"
                )

            seen.add(key)

        return self


class WorkflowTransitionRecord(BaseModel):
    """Audit record for one successful state transition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    event: str
    target: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class WorkflowRun(BaseModel):
    """Tracks one execution of a workflow."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_name: str = Field(min_length=1)
    workflow_version: str = Field(min_length=1)

    current_state: str = Field(min_length=1)

    status: Literal[
        "pending",
        "running",
        "waiting_for_approval",
        "completed",
        "failed",
        "cancelled",
    ] = "pending"

    context: dict[str, Any] = Field(default_factory=dict)
    transition_history: list[WorkflowTransitionRecord] = Field(
        default_factory=list
    )

    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
