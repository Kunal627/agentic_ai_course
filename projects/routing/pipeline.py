
from .classifier import IntentClassifier
from .models import RoutingDecision, RoutingRequest
from .router import CapabilityRouter



class RoutingPipeline:
    """Classify a request and route only when confidence is sufficient."""

    def __init__(
        self,
        classifier: IntentClassifier,
        router: CapabilityRouter,
        confidence_threshold: float = 0.80,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")

        self.classifier = classifier
        self.router = router
        self.confidence_threshold = confidence_threshold


    def execute(self, request: RoutingRequest) -> RoutingDecision:
        supported_intents = self.router.registry.supported_intents()

        classification = self.classifier.classify(
            request,
            supported_intents,
        )

        if (
            classification.intent == "unknown_intent"
            or classification.intent not in supported_intents
            or classification.confidence < self.confidence_threshold
        ):
            return RoutingDecision(
                request_id=request.request_id,
                status="not_routed",
                specialist_name=None,
                reason=(
                    "Classification was uncertain or unsupported: "
                    f"{classification.reason}"
                ),
                confidence=classification.confidence,
                matched_capability=None,
            )

        normalized_request = RoutingRequest(
            request_id=request.request_id,
            intent=classification.intent,
            message=request.message or request.intent,
            payload=request.payload,
        )

        return self.router.route(normalized_request)



