
from routing.classifier import IntentClassifier
from routing.models import IntentClassification, RoutingRequest


class RuleBasedIntentClassifier:
    """Classify requests using simple keyword rules."""

    def classify(
        self,
        request: RoutingRequest,
        supported_intents: frozenset[str],
    ) -> IntentClassification:
        text = request.text_to_classify.lower()

        predicted_intent = None
        reason = ""

        if "protocol" in text:
            predicted_intent = "protocol_review"
            reason = "The request contains the keyword 'protocol'."
        elif "eligibility" in text or "eligible" in text:
            predicted_intent = "eligibility_evaluation"
            reason = "The request contains an eligibility-related keyword."

        if predicted_intent not in supported_intents:
            return IntentClassification(
                intent="unknown_intent",
                confidence=0.0,
                reason="No supported intent could be identified.",
            )

        return IntentClassification(
            intent=predicted_intent,
            confidence=0.95,
            reason=reason,
        )
