
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .workflows import HelloWorkflow, ProtocolValidationWorkflow
from .activities import validate_protocol, review_protocol


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="deterministic-ai-workflow",
        workflows=[HelloWorkflow, ProtocolValidationWorkflow],
        activities=[validate_protocol, review_protocol],
    )

    print("Worker started. Waiting for workflows...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
