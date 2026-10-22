
import asyncio

from temporalio.client import Client

from .workflows import ProtocolValidationWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    workflow_id = input("Enter workflow ID: ").strip()
    decision = input("Approve the review? (yes/no): ").strip().lower()

    if decision not in {"yes", "no"}:
        print("Please enter 'yes' or 'no'.")
        return

    reviewer = input("Reviewer identifier: ").strip()
    comment = input("Approval/rejection comment: ").strip()

    if not reviewer:
        print("Reviewer identifier must not be empty.")
        return

    handle = client.get_workflow_handle(workflow_id)

    await handle.signal(
        ProtocolValidationWorkflow.submit_approval,
        args=[decision == "yes", reviewer, comment],
    )

    print("Decision signal sent. Waiting for workflow result...")

    result = await handle.result()
    print("Final workflow result:", result)


if __name__ == "__main__":
    asyncio.run(main())
