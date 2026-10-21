
from dataclasses import dataclass, field

from agent_runtime.tools.errors import ToolPolicyError


@dataclass(frozen=True)
class ToolPolicy:
    """Defines which registered tools are permitted to execute."""

    allowed_tools: frozenset[str] = field(default_factory=frozenset)

    def check(self, tool_name: str) -> None:
        """Raise an error if the tool is not explicitly allowed."""
        if tool_name not in self.allowed_tools:
            raise ToolPolicyError(
                f"Execution of tool '{tool_name}' is not permitted."
            )
