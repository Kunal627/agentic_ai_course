
from dataclasses import dataclass

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.errors import ToolNotFoundError


@dataclass(frozen=True)
class ResolvedTool:
    """A registered tool paired with its definition."""

    definition: ToolDefinition
    implementation: BaseTool


class ToolResolver:
    """Resolves tool names to registered definitions and implementations."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def resolve(self, name: str) -> ResolvedTool:
        """Return the registered tool and its metadata."""
        try:
            definition = self._registry.get_definition(name)
            implementation = self._registry.get_tool(name)
        except KeyError:
            raise ToolNotFoundError(
                f"Tool '{name}' is not registered."
            ) from None

        return ResolvedTool(
            definition=definition,
            implementation=implementation,
        )
