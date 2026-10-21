
import asyncio

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.registry import ToolRegistry


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

tool = AddTool()
registry = ToolRegistry()

registry.register(definition, tool)

# Verify that the implementation and metadata are retrievable.
assert registry.get_tool("calculator.add") is tool
assert registry.get_definition("calculator.add") == definition

# Verify that the registered tool can execute.
result = asyncio.run(
    registry.get_tool("calculator.add").execute({"a": 10, "b": 20})
)
assert result == 30

# Verify that metadata can be listed.
assert len(registry.list_definitions()) == 1

print("Registry test passed.")
print("Registered tools:", [d.name for d in registry.list_definitions()])
print("Execution result:", result)
