
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agent_runtime.models.messages import Message
from agent_runtime.tools.execution import ToolExecutionResult


class RunState(BaseModel):
    """Tracks the progress and outcome of one agent execution."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    run_id: str = Field(default_factory=lambda: str(uuid4()))

    messages: list[Message] = Field(default_factory=list)
    tool_executions: list[ToolExecutionResult] = Field(default_factory=list)
    step_count: int = Field(default=0, ge=0)

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)

    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
    ] = "pending"

    final_answer: str | None = None
    error: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None



    def start(self) -> None:
        if self.status == "running":
            return
    
        if self.status != "pending":
            raise ValueError(
                f"Cannot start a run in '{self.status}' state."
            )
    
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)



    def complete(self, answer: str) -> None:
        if self.status != "running":
            raise ValueError(
                f"Cannot complete a run in '{self.status}' state."
            )

        self.status = "completed"
        self.final_answer = answer
        self.completed_at = datetime.now(timezone.utc)


    def fail(self, error: str) -> None:
        if self.status != "running":
            raise ValueError(
                f"Cannot fail a run in '{self.status}' state."
            )

        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now(timezone.utc)


    def cancel(self, reason: str = "Run cancelled.") -> None:
        if self.status not in ("pending", "running"):
            raise ValueError(
                f"Cannot cancel a run in '{self.status}' state."
            )

        self.status = "cancelled"
        self.error = reason
        self.completed_at = datetime.now(timezone.utc)



