
import asyncio

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver
from agent_runtime.tools.retry import RetryPolicy


class FlakyTool(BaseTool):
    """Fails twice, then succeeds."""

    def __init__(self):
        self.attempts = 0

    async def execute(self, arguments: dict) -> int:
        self.attempts += 1

        if self.attempts < 3:
            raise ConnectionError("Temporary failure")

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
        retry_safe=True,
    )

    tool = FlakyTool()
    registry = ToolRegistry()
    registry.register(definition, tool)

    dispatcher = ToolDispatcher(
        ToolResolver(registry),
        ToolPolicy(allowed_tools=frozenset({"calculator.add"})),
        timeout_seconds=2.0,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "success", result.model_dump()
    assert result.output == 30
    assert tool.attempts == 3

    print("Retry integration test passed.")
    print("Attempts:", tool.attempts)
    print("Result:", result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
