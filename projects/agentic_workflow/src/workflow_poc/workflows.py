
from temporalio import workflow
from datetime import timedelta
from typing import Any
from .models import AIReviewResult, ReviewDisposition
from .policies import evaluate_review
from temporalio.common import RetryPolicy

@workflow.defn
class HelloWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Hello, {name}! Temporal workflow completed."



@workflow.defn
class ProtocolValidationWorkflow:
    def __init__(self) -> None:
        self._approval_received = False
        self._approved: bool | None = None
        self._reviewer: str | None = None
        self._approval_comment: str | None = None

    @workflow.signal
    async def submit_approval(
        self,
        approved: bool,
        reviewer: str,
        comment: str = "",
    ) -> None:
        if self._approval_received:
            return

        self._approval_received = True
        self._approved = approved
        self._reviewer = reviewer
        self._approval_comment = comment

    @workflow.run
    async def run(
        self,
        protocol_data: dict[str, Any],
    ) -> dict[str, Any]:
        validation = await workflow.execute_activity(
            "validate_protocol",
            args=[protocol_data],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        )

        if not validation["valid"]:
            return {
                "status": "rejected",
                "protocol_id": validation.get("protocol_id"),
                "message": "Protocol failed input validation.",
                "errors": validation["errors"],
            }

        raw_review = await workflow.execute_activity(
            "review_protocol",
            args=[protocol_data],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        )

        review = AIReviewResult.model_validate(raw_review)
        decision = evaluate_review(review)

        if decision.disposition == ReviewDisposition.REQUIRES_HUMAN_REVIEW:
            await workflow.wait_condition(lambda: self._approval_received)

            status = "completed" if self._approved else "rejected"
            message = (
                "Review approved by a human."
                if self._approved
                else "Review rejected by a human."
            )

            approval = {
                "approved": self._approved,
                "reviewer": self._reviewer,
                "comment": self._approval_comment,
            }
        else:
            status = "completed"
            message = "Review completed without requiring human approval."
            approval = None

        return {
            "status": status,
            "protocol_id": validation["protocol_id"],
            "message": message,
            "review": review.model_dump(mode="json"),
            "policy_decision": decision.model_dump(mode="json"),
            "approval": approval,
        }
