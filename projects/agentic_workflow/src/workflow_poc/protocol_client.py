
import asyncio
from uuid import uuid4

from temporalio.client import Client

from .workflows import ProtocolValidationWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    protocol = {
        "protocol_id": "PROTO-001",
        "title": "Synthetic Research Protocol",
        "objective": "Evaluate a hypothetical research intervention.",
        "study_design": "Observational cohort study",
        "population": "Adults aged 18 years and older",
        "inclusion_criteria": [
            "Age 18 years or older",
            "Able to provide informed consent",
        ],
        "exclusion_criteria": [
            "Unable to complete the study procedures",
        ],
        "endpoints": [
            "Primary outcome measured at 12 weeks",
        ],
    }

    workflow_id = f"protocol-review-{uuid4()}"

    await client.start_workflow(
        ProtocolValidationWorkflow.run,
        args=[protocol],
        id=workflow_id,
        task_queue="deterministic-ai-workflow",
    )

    print("Workflow started.")
    print(f"Workflow ID: {workflow_id}")
    print("Use this ID to submit the human decision.")


if __name__ == "__main__":
    asyncio.run(main())
