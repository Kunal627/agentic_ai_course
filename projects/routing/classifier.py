
from typing import Protocol

from .models import IntentClassification, RoutingRequest


class IntentClassifier(Protocol):
    """Interface for classifying requests into supported intents."""

    def classify(
        self,
        request: RoutingRequest,
        supported_intents: frozenset[str],
    ) -> IntentClassification:
        """Classify a request using the available intent names."""
        ...
