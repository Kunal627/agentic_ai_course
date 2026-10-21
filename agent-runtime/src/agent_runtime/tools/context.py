
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    """Metadata describing one attempt of a logical tool operation."""

    operation_id: str
    attempt_number: int
