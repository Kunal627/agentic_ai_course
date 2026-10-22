
import asyncio
from uuid import uuid4

from temporalio.client import Client

from .workflows import HelloWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        HelloWorkflow.run,
        "Research Team",
        id=f"hello-workflow-{uuid4()}",
        task_queue="deterministic-ai-workflow",
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
