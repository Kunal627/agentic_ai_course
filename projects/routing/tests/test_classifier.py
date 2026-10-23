
from routing.classifier import IntentClassifier
from routing.models import IntentClassification, RoutingRequest



class FakeIntentClassifier:
    def classify(
        self,
        request: RoutingRequest,
        supported_intents: frozenset[str],
    ) -> IntentClassification:
        return IntentClassification(
            intent="protocol_review",
            confidence=0.95,
            reason="The request asks for a protocol review.",
        )


def test_fake_classifier_implements_classifier_interface():
    classifier: IntentClassifier = FakeIntentClassifier()

    request = RoutingRequest(
        request_id="req-001",
        intent="Review this clinical trial protocol.",
    )

    result = classifier.classify(request, supported_intents=frozenset({"protocol_review", "eligibility_evaluation"}))

    assert result.intent == "protocol_review"
    assert result.confidence == 0.95
    assert "protocol review" in result.reason
