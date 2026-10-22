
from .models import (
    AIReviewResult,
    FindingSeverity,
    PolicyDecision,
    ReviewDisposition,
)


def evaluate_review(result: AIReviewResult) -> PolicyDecision:
    """Apply fixed rules to a validated AI review."""

    reasons: list[str] = []

    if result.confidence < 0.80:
        reasons.append("AI confidence is below the configured threshold")

    high_severity_count = sum(
        finding.severity == FindingSeverity.HIGH
        for finding in result.findings
    )

    if high_severity_count > 0:
        reasons.append("One or more high-severity findings require human review")

    if reasons:
        return PolicyDecision(
            disposition=ReviewDisposition.REQUIRES_HUMAN_REVIEW,
            reasons=reasons,
        )

    return PolicyDecision(
        disposition=ReviewDisposition.REPORT_ONLY,
        reasons=["No configured rule requires human review"],
    )
