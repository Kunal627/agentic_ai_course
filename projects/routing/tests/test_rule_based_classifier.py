
from routing.models import RoutingRequest
from routing.rule_based_classifier import RuleBasedIntentClassifier


def test_classifies_protocol_review():
    supported_intents = frozenset({
    "protocol_review",
    "eligibility_evaluation",
        })
    classifier = RuleBasedIntentClassifier()

    request = RoutingRequest(
        request_id="req-001",
        intent="Please review this clinical trial protocol.",
    )

    result = classifier.classify(request, supported_intents=supported_intents)

    assert result.intent == "protocol_review"
    assert result.confidence == 0.95


def test_classifies_eligibility_evaluation():
    classifier = RuleBasedIntentClassifier()
    supported_intents = frozenset({
    "protocol_review",
    "eligibility_evaluation",
    })
    request = RoutingRequest(
        request_id="req-002",
        intent="Evaluate patient eligibility for this study.",
    )

    result = classifier.classify(request, supported_intents=supported_intents)

    assert result.intent == "eligibility_evaluation"
    assert result.confidence == 0.95


def test_unknown_request_returns_unknown_intent():
    classifier = RuleBasedIntentClassifier()
    supported_intents = frozenset({
        "protocol_review",
        "eligibility_evaluation",
    })

    request = RoutingRequest(
        request_id="req-003",
        intent="Calculate the cost of a server.",
    )

    result = classifier.classify(request, supported_intents=supported_intents)

    assert result.intent == "unknown_intent"
    assert result.confidence == 0.0
