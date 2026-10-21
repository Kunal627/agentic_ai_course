
from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition


class ToolRegistry:
    """Stores explicitly registered tools and their definitions."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._definitions: dict[str, ToolDefinition] = {}

    def register(
        self,
        definition: ToolDefinition,
        tool: BaseTool,
    ) -> None:
        """Register a tool implementation and its metadata."""
        if definition.name in self._tools:
            raise ValueError(
                f"Tool '{definition.name}' is already registered."
            )

        self._tools[definition.name] = tool
        self._definitions[definition.name] = definition

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve a registered tool implementation."""
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(f"Tool '{name}' is not registered.") from None

    def get_definition(self, name: str) -> ToolDefinition:
        """Retrieve metadata for a registered tool."""
        try:
            return self._definitions[name]
        except KeyError:
            raise KeyError(f"Tool '{name}' is not registered.") from None

    def list_definitions(self) -> list[ToolDefinition]:
        """List metadata for all registered tools."""
        return list(self._definitions.values())
