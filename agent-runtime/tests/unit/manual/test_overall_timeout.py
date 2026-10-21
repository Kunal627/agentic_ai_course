
import asyncio
import time

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver
from agent_runtime.tools.retry import RetryPolicy


class FlakySlowTool(BaseTool):
    def __init__(self):
        self.attempts = 0

    async def execute(self, arguments: dict) -> str:
        self.attempts += 1

        if self.attempts == 1:
            raise ConnectionError("Temporary failure")

        await asyncio.sleep(2)
        return "Finished"


async def main():
    definition = ToolDefinition(
        name="test.slow",
        description="Fails and then runs slowly.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={"type": "string"},
        risk_level="low",
    )

    tool = FlakySlowTool()
    registry = ToolRegistry()
    registry.register(definition, tool)

    dispatcher = ToolDispatcher(
        ToolResolver(registry),
        ToolPolicy(allowed_tools=frozenset({"test.slow"})),
        timeout_seconds=1.0,
        overall_timeout_seconds=0.2,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.05,
            backoff_multiplier=2.0,
            retryable_errors=(ConnectionError,),
        ),
    )

    start = time.perf_counter()
    result = await dispatcher.dispatch("test.slow", {})
    elapsed = time.perf_counter() - start

    print("Result:", result.model_dump())
    print(f"Elapsed seconds: {elapsed:.3f}")
    print(f"Attempts started: {tool.attempts}")

    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"
    assert "overall timeout" in result.error_message
    assert elapsed < 0.8

    print("Overall deadline test passed.")


if __name__ == "__main__":
    asyncio.run(main())
