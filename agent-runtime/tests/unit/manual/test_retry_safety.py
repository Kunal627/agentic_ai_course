
import asyncio

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver
from agent_runtime.tools.retry import RetryPolicy


class FlakyTool(BaseTool):
    def __init__(self):
        self.attempts = 0

    async def execute(self, arguments: dict) -> int:
        self.attempts += 1
        raise ConnectionError("Temporary failure")


async def main():
    definition = ToolDefinition(
        name="operation.unsafe",
        description="An operation that is not approved for automatic retries.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={"type": "integer"},
        risk_level="medium",
        # retry_safe intentionally omitted; defaults to False.
    )

    tool = FlakyTool()
    registry = ToolRegistry()
    registry.register(definition, tool)

    dispatcher = ToolDispatcher(
        ToolResolver(registry),
        ToolPolicy(allowed_tools=frozenset({"operation.unsafe"})),
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch("operation.unsafe", {})

    assert result.status == "error"
    assert result.error_type == "ToolExecutionError"
    assert tool.attempts == 1

    print("Unsafe tool was not retried.")
    print("Attempts:", tool.attempts)
    print("Retry safety test passed.")


if __name__ == "__main__":
    asyncio.run(main())
