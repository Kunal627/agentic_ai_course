
from .models import RoutingDecision, RoutingRequest
from .registry import SpecialistRegistry


class CapabilityRouter:
    """Routes requests using registered capabilities and an optional fallback."""

    def __init__(
        self,
        registry: SpecialistRegistry,
        fallback_specialist: str | None = None,
    ) -> None:
        self._registry = registry
        self._fallback_specialist = fallback_specialist

        if fallback_specialist is not None:
            if registry.get(fallback_specialist) is None:
                raise ValueError(
                    f"Fallback specialist is not registered: "
                    f"{fallback_specialist}"
                )

    
    @property
    def registry(self) -> SpecialistRegistry:
        """Expose the specialist registry for read-only lookup."""
        return self._registry


    def route(self, request: RoutingRequest) -> RoutingDecision:
        specialist = self._registry.find_by_capability(request.intent)

        if specialist is not None:
            return RoutingDecision(
                request_id=request.request_id,
                status="routed",
                specialist_name=specialist.name,
                reason=(
                    f"Matched intent '{request.intent}' "
                    "to a registered capability."
                ),
                confidence=1.0,
                matched_capability=request.intent,
            )

        if self._fallback_specialist is not None:
            return RoutingDecision(
                request_id=request.request_id,
                status="routed",
                specialist_name=self._fallback_specialist,
                reason=(
                    f"No direct match for '{request.intent}'; "
                    "using configured fallback."
                ),
                confidence=0.0,
                matched_capability=None,
            )

        return RoutingDecision(
            request_id=request.request_id,
            status="not_routed",
            specialist_name=None,
            reason=f"No specialist supports intent: {request.intent}",
            confidence=0.0,
            matched_capability=None,
        )
