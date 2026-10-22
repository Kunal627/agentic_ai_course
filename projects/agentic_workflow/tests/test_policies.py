
import pytest
from pydantic import ValidationError
from src.workflow_poc.models import (
    AIReviewResult,
    FindingSeverity,
    ProtocolInput,
    ReviewDisposition,
    ReviewFinding,
)
from src.workflow_poc.policies import evaluate_review


def make_result(
    confidence: float = 0.95,
    severity: FindingSeverity = FindingSeverity.LOW,
) -> AIReviewResult:
    return AIReviewResult(
        confidence=confidence,
        findings=[
            ReviewFinding(
                code="MISSING_DETAIL",
                description="A section may need clarification.",
                severity=severity,
                evidence="Synthetic example evidence.",
            )
        ],
    )


def test_low_severity_and_high_confidence_does_not_require_review():
    decision = evaluate_review(make_result())

    assert decision.disposition == ReviewDisposition.REPORT_ONLY


def test_low_confidence_requires_human_review():
    decision = evaluate_review(make_result(confidence=0.65))

    assert decision.disposition == ReviewDisposition.REQUIRES_HUMAN_REVIEW


def test_high_severity_requires_human_review():
    decision = evaluate_review(
        make_result(severity=FindingSeverity.HIGH)
    )

    assert decision.disposition == ReviewDisposition.REQUIRES_HUMAN_REVIEW


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        make_result(confidence=1.5)


def test_unexpected_ai_output_field_is_rejected():
    with pytest.raises(ValidationError):
        AIReviewResult(
            confidence=0.95,
            findings=[],
            approve_protocol=True,
        )
