from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Any


class RoutingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    intent: str | None = Field(default=None, min_length=1)
    message: str | None = Field(default=None, min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    @property
    def text_to_classify(self) -> str:
        text = self.message or self.intent
        if text is None:
            raise ValueError("Either message or intent must be provided")
        return text

    
class RoutingDecision(BaseModel):
    """The router's decision about where a request should go."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    status: Literal["routed", "not_routed"] = Field()
    specialist_name: str | None = None
    reason: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    matched_capability: str | None = None


class IntentClassification(BaseModel):
    """Represents the classification of an intent with a confidence score."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)