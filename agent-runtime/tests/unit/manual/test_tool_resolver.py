
from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.errors import ToolNotFoundError
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver


class AddTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        return arguments["a"] + arguments["b"]


definition = ToolDefinition(
    name="calculator.add",
    description="Add two numbers.",
    version="1.0.0",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
        "additionalProperties": False,
    },
    output_schema={"type": "number"},
    risk_level="low",
)

registry = ToolRegistry()
tool = AddTool()
registry.register(definition, tool)

resolver = ToolResolver(registry)

resolved = resolver.resolve("calculator.add")
assert resolved.definition == definition
assert resolved.implementation is tool

print("Registered tool resolved successfully.")

try:
    resolver.resolve("filesystem.delete")
except ToolNotFoundError:
    print("Unknown tool correctly rejected.")
else:
    raise AssertionError("Unknown tool was unexpectedly resolved.")

print("Tool resolver tests passed.")
