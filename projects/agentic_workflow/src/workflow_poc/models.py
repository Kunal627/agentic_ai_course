
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(StrEnum):
    RECEIVED = "received"
    VALIDATING = "validating"
    AI_REVIEW = "ai_review"
    POLICY_CHECK = "policy_check"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class ProtocolInput(BaseModel):
    """Synthetic research protocol used by the POC."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    protocol_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=2000)
    study_design: str = Field(min_length=1, max_length=200)
    population: str = Field(min_length=1, max_length=1000)
    inclusion_criteria: list[str] = Field(min_length=1)
    exclusion_criteria: list[str] = Field(min_length=1)
    endpoints: list[str] = Field(min_length=1)


class FindingSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewFinding(BaseModel):
    """One potential issue identified during document review."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    severity: FindingSeverity
    evidence: str = Field(min_length=1, max_length=2000)


class AIReviewResult(BaseModel):
    """Structured output expected from the AI reviewer."""

    model_config = ConfigDict(extra="forbid")

    findings: list[ReviewFinding]
    confidence: float = Field(ge=0.0, le=1.0)


class ReviewDisposition(StrEnum):
    REPORT_ONLY = "report_only"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class PolicyDecision(BaseModel):
    disposition: ReviewDisposition
    reasons: list[str]
