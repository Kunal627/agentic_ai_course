
import pytest
from pydantic import ValidationError

from routing.models import RoutingDecision, RoutingRequest, IntentClassification


def test_routing_request_accepts_valid_input():
    request = RoutingRequest(
        request_id="req-001",
        intent="protocol_review",
        payload={"protocol_id": "PROTO-001"},
    )

    assert request.request_id == "req-001"
    assert request.intent == "protocol_review"
    assert request.payload["protocol_id"] == "PROTO-001"


def test_routing_request_rejects_empty_intent():
    with pytest.raises(ValidationError):
        RoutingRequest(
            request_id="req-001",
            intent="",
        )


def test_routing_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RoutingRequest(
            request_id="req-001",
            intent="protocol_review",
            unexpected="value",
        )


def test_routing_decision_accepts_no_route():
    decision = RoutingDecision(
        request_id="req-001",
        status="not_routed",
        specialist_name=None,
        reason="No specialist supports this intent.",
        confidence=0.0,
        matched_capability=None,
    )

    assert decision.status == "not_routed"
    assert decision.specialist_name is None
    assert decision.confidence == 0.0
    assert decision.matched_capability is None


def test_intent_classification_accepts_valid_result():
    result = IntentClassification(
        intent="protocol_review",
        confidence=0.94,
        reason="The request asks for a protocol review.",
    )

    assert result.intent == "protocol_review"
    assert result.confidence == 0.94
    assert "protocol review" in result.reason


def test_intent_classification_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        IntentClassification(
            intent="protocol_review",
            confidence=1.2,
            reason="Protocol review request.",
        )


def test_intent_classification_rejects_negative_confidence():
    with pytest.raises(ValidationError):
        IntentClassification(
            intent="protocol_review",
            confidence=-0.1,
            reason="Protocol review request.",
        )


def test_intent_classification_rejects_empty_intent():
    with pytest.raises(ValidationError):
        IntentClassification(
            intent="",
            confidence=0.8,
            reason="Some reason.",
        )
