import asyncio
from typing import Any
from agent_runtime.tools.base import BaseTool

class AddTool(BaseTool):
    async def execute(self, args: dict[str, Any]) -> Any:
        """Execute the AddTool with the given arguments."""
        a = args.get("a")
        b = args.get("b")
        if a is None or b is None:
            raise ValueError("Both 'a' and 'b' must be provided.")
        return a + b


async def main() -> None:
    tool = AddTool()
    result = await tool.execute({"a": 5, "b": 10})
    print(f"Result of addition: {result}")

if __name__ == "__main__":
    asyncio.run(main())