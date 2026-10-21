
import asyncio

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver


class AddTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        return arguments["a"] + arguments["b"]


async def main():
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
    registry.register(definition, AddTool())

    resolver = ToolResolver(registry)
    policy = ToolPolicy(
        allowed_tools=frozenset({"calculator.add"})
    )
    dispatcher = ToolDispatcher(resolver, policy)

    # Successful execution
    result = await dispatcher.dispatch(
        "calculator.add", {"a": 10, "b": 20}
    )
    assert result.status == "success"
    assert result.output == 30
    print("Successful execution:", result.model_dump())

    # Invalid arguments
    result = await dispatcher.dispatch(
        "calculator.add", {"a": 10}
    )
    assert result.status == "error"
    assert result.error_type == "ToolValidationError"
    print("Invalid arguments rejected.")

    # Tool not registered
    result = await dispatcher.dispatch(
        "filesystem.delete", {}
    )
    assert result.status == "error"
    assert result.error_type == "ToolNotFoundError"
    print("Unknown tool rejected.")

    # Registered but not allowed
    restricted_dispatcher = ToolDispatcher(
        resolver,
        ToolPolicy(allowed_tools=frozenset()),
    )
    result = await restricted_dispatcher.dispatch(
        "calculator.add", {"a": 10, "b": 20}
    )
    assert result.status == "error"
    assert result.error_type == "ToolPolicyError"
    print("Policy enforcement verified.")

    print("Tool dispatcher tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
