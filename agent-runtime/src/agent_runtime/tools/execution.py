
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolExecutionResult(BaseModel):
    """Normalized result of one tool execution."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    operation_id: str
    status: Literal["success", "error", "timeout"]
    output: Any = None
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    attempts: int = Field(default=0, ge=0)
