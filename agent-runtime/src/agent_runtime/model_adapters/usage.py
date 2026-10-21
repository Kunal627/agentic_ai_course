
from pydantic import BaseModel, ConfigDict, Field


class UsageRecord(BaseModel):
    """Token usage and estimated cost for a model call."""

    model_config = ConfigDict(extra="forbid")

    model: str

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    input_cost_usd: float = Field(default=0.0, ge=0)
    output_cost_usd: float = Field(default=0.0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def total_cost_usd(self) -> float:
        return self.input_cost_usd + self.output_cost_usd


class UsageTracker:
    """Accumulates usage across multiple model calls in one run."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.estimated_cost_usd = 0.0

    def record(self, usage: UsageRecord) -> None:
        """Add one model call's usage to the running totals."""
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.estimated_cost_usd += usage.total_cost_usd
