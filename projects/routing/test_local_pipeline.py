from .llm_classifier import LLMIntentClassifier
from .models import RoutingRequest
from .pipeline import RoutingPipeline
from .registry import Specialist, SpecialistRegistry
from .router import CapabilityRouter


def main() -> None:
    registry = SpecialistRegistry()

    registry.register(
        Specialist(
            name="protocol_specialist",
            capabilities=frozenset({"protocol_review"}),
        )
    )

    registry.register(
        Specialist(
            name="eligibility_specialist",
            capabilities=frozenset({"eligibility_evaluation"}),
        )
    )

    router = CapabilityRouter(registry)
    classifier = LLMIntentClassifier()

    pipeline = RoutingPipeline(
        classifier=classifier,
        router=router,
        confidence_threshold=0.80,
    )

    request = RoutingRequest(
        request_id="req-pipeline-001",
        message=(
            "Review the clinical trial protocol for safety risks, "
            "missing sections, and compliance issues."
        ),
    )

    decision = pipeline.execute(request)

    print("Routing status:", decision.status)
    print("Selected specialist:", decision.specialist_name)
    print("Matched capability:", decision.matched_capability)
    print("Confidence:", decision.confidence)
    print("Reason:", decision.reason)


if __name__ == "__main__":
    main()