
import json
from unittest.mock import MagicMock

import pytest

from routing.llm_classifier import LLMIntentClassifier
from routing.models import RoutingRequest


@pytest.fixture
def classifier():
    return LLMIntentClassifier()


def make_response(content: str):
    response = MagicMock()
    response.choices[0].message.content = content
    return response


def test_classifies_protocol_review(classifier):
    classifier.client.chat.completions.create = MagicMock(
        return_value=make_response(
            json.dumps({
                "intent": "protocol_review",
                "confidence": 0.95,
                "reason": "The request asks for a protocol review.",
            })
        )
    )

    result = classifier.classify(
        RoutingRequest(
            request_id="req-001",
            intent="Review this clinical trial protocol.",
        ),
        frozenset({"protocol_review", "eligibility_evaluation"}),
    )

    assert result.intent == "protocol_review"
    assert result.confidence == 0.95


def test_unsupported_intent_is_rejected(classifier):
    classifier.client.chat.completions.create = MagicMock(
        return_value=make_response(
            json.dumps({
                "intent": "delete_all_records",
                "confidence": 0.99,
                "reason": "Unsupported prediction.",
            })
        )
    )

    result = classifier.classify(
        RoutingRequest(
            request_id="req-002",
            intent="Delete all records.",
        ),
        frozenset({"protocol_review"}),
    )

    assert result.intent == "unknown_intent"
    assert result.confidence == 0.0


def test_empty_llm_response_is_rejected(classifier):
    classifier.client.chat.completions.create = MagicMock(
        return_value=make_response("")
    )

    with pytest.raises(ValueError, match="empty classification"):
        classifier.classify(
            RoutingRequest(
                request_id="req-003",
                intent="Review this protocol.",
            ),
            frozenset({"protocol_review"}),
        )


def test_invalid_json_is_rejected(classifier):
    classifier.client.chat.completions.create = MagicMock(
        return_value=make_response("not valid json")
    )

    with pytest.raises(json.JSONDecodeError):
        classifier.classify(
            RoutingRequest(
                request_id="req-004",
                intent="Review this protocol.",
            ),
            frozenset({"protocol_review"}),
        )


def test_empty_supported_intents_does_not_call_llm(classifier):
    classifier.client.chat.completions.create = MagicMock()

    result = classifier.classify(
        RoutingRequest(
            request_id="req-005",
            intent="Review this protocol.",
        ),
        frozenset(),
    )

    assert result.intent == "unknown_intent"
    assert result.confidence == 0.0
    classifier.client.chat.completions.create.assert_not_called()
