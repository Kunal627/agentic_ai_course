
import asyncio

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver


class SlowTool(BaseTool):
    async def execute(self, arguments: dict) -> str:
        await asyncio.sleep(2)
        return "Finished"


async def main():
    definition = ToolDefinition(
        name="test.slow",
        description="A deliberately slow tool.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={"type": "string"},
        risk_level="low",
    )

    registry = ToolRegistry()
    registry.register(definition, SlowTool())

    dispatcher = ToolDispatcher(
        ToolResolver(registry),
        ToolPolicy(allowed_tools=frozenset({"test.slow"})),
        timeout_seconds=0.2,
    )

    result = await dispatcher.dispatch("test.slow", {})
    print("Actual dispatcher result:", result.model_dump())
    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"
    assert result.duration_ms < 1000

    print("Timeout handled successfully.")
    print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
