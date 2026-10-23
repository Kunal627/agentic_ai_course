
from .llm_classifier import LLMIntentClassifier
from .models import RoutingRequest


def main() -> None:
    classifier = LLMIntentClassifier()

    request = RoutingRequest(
        request_id="req-local-001",
        intent="natural_language_request",
        message=(
            "Review the clinical trial protocol for safety risks, "
            "missing sections, and compliance issues."
        ),
    )

    supported_intents = frozenset({
        "protocol_review",
        "eligibility_evaluation",
    })

    result = classifier.classify(
        request,
        supported_intents,
    )

    print("Predicted intent:", result.intent)
    print("Confidence:", result.confidence)
    print("Reason:", result.reason)


if __name__ == "__main__":
    main()
