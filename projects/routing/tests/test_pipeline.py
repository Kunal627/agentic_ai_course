
from routing.pipeline import RoutingPipeline
from routing.rule_based_classifier import RuleBasedIntentClassifier
from routing.registry import Specialist, SpecialistRegistry
from routing.router import CapabilityRouter
from routing.models import RoutingRequest, IntentClassification
import pytest

def test_natural_language_request_is_classified_and_routed():
    registry = SpecialistRegistry()

    registry.register(
        Specialist(
            name="protocol_specialist",
            capabilities=frozenset({"protocol_review"}),
        )
    )

    router = CapabilityRouter(registry)
    classifier = RuleBasedIntentClassifier()
    pipeline = RoutingPipeline(classifier, router)

    request = RoutingRequest(
        request_id="req-100",
        intent="natural_language_request",
        message="Please review this clinical trial protocol.",
    )

    decision = pipeline.execute(request)

    assert decision.status == "routed"
    assert decision.specialist_name == "protocol_specialist"
    assert decision.matched_capability == "protocol_review"
    assert decision.confidence == 1.0



class FixedClassifier:
    def __init__(self, intent: str, confidence: float):
        self.intent = intent
        self.confidence = confidence

    def classify(
        self,
        request: RoutingRequest,
        supported_intents: frozenset[str],
    ) -> IntentClassification:
        return IntentClassification(
            intent=self.intent,
            confidence=self.confidence,
            reason="Fixed classification for testing.",
        )

def build_test_router() -> CapabilityRouter:
    registry = SpecialistRegistry()
    registry.register(
        Specialist(
            name="protocol_specialist",
            capabilities=frozenset({"protocol_review"}),
        )
    )
    return CapabilityRouter(registry)


def test_low_confidence_classification_is_not_routed():
    pipeline = RoutingPipeline(
        classifier=FixedClassifier("protocol_review", 0.50),
        router=build_test_router(),
        confidence_threshold=0.80,
    )

    decision = pipeline.execute(
        RoutingRequest(
            request_id="req-low",
            intent="Review this protocol",
        )
    )

    assert decision.status == "not_routed"
    assert decision.specialist_name is None
    assert decision.confidence == 0.50
    assert decision.matched_capability is None


def test_unknown_intent_is_not_routed():
    pipeline = RoutingPipeline(
        classifier=FixedClassifier("unknown_intent", 0.99),
        router=build_test_router(),
    )

    decision = pipeline.execute(
        RoutingRequest(
            request_id="req-unknown",
            intent="Do something unrelated",
        )
    )

    assert decision.status == "not_routed"
    assert decision.specialist_name is None


def test_invalid_confidence_threshold_is_rejected():
    with pytest.raises(ValueError, match="confidence_threshold"):
        RoutingPipeline(
            classifier=FixedClassifier("protocol_review", 0.95),
            router=build_test_router(),
            confidence_threshold=1.5,
        )

def test_unsupported_intent_is_not_routed_even_with_high_confidence():
    pipeline = RoutingPipeline(
        classifier=FixedClassifier(
            "delete_all_records",
            0.99,
        ),
        router=build_test_router(),
        confidence_threshold=0.80,
    )
    decision = pipeline.execute(
        RoutingRequest(
            request_id="req-unsupported",
            intent="Delete all records.",
        )
    )
    assert decision.status == "not_routed"
    assert decision.specialist_name is None
    assert decision.matched_capability is None
    assert decision.confidence == 0.99
    assert "unsupported" in decision.reason.lower()