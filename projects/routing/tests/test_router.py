import pytest

from routing.models import RoutingRequest
from routing.registry import Specialist, SpecialistRegistry
from routing.router import CapabilityRouter


def build_router() -> CapabilityRouter:
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

    return CapabilityRouter(registry)


def test_routes_protocol_review():
    router = build_router()

    request = RoutingRequest(
        request_id="req-001",
        intent="protocol_review",
    )

    decision = router.route(request)

    assert decision.status == "routed"
    assert decision.request_id == "req-001"
    assert decision.specialist_name == "protocol_specialist"
    assert decision.reason
    assert decision.confidence == 1.0
    assert decision.matched_capability == "protocol_review"


def test_routes_eligibility_evaluation():
    router = build_router()

    request = RoutingRequest(
        request_id="req-002",
        intent="eligibility_evaluation",
    )

    decision = router.route(request)

    assert decision.status == "routed"
    assert decision.request_id == "req-002"
    assert decision.specialist_name == "eligibility_specialist"
    assert decision.reason
    assert decision.confidence == 1.0
    assert decision.matched_capability == "eligibility_evaluation"


def test_unknown_intent_returns_not_routed():
    router = build_router()

    request = RoutingRequest(
        request_id="req-003",
        intent="unknown_intent",
    )

    decision = router.route(request)

    assert decision.status == "not_routed"
    assert decision.request_id == "req-003"
    assert decision.specialist_name is None
    assert "No specialist supports intent" in decision.reason
    assert decision.confidence == 0.0
    assert decision.matched_capability is None


def test_unknown_intent_uses_configured_fallback():
    registry = SpecialistRegistry()

    registry.register(
        Specialist(
            name="general_specialist",
            capabilities=frozenset({"general_assistance"}),
        )
    )

    router = CapabilityRouter(
        registry,
        fallback_specialist="general_specialist",
    )

    request = RoutingRequest(
        request_id="req-004",
        intent="unknown_intent",
    )

    decision = router.route(request)

    assert decision.status == "routed"
    assert decision.request_id == "req-004"
    assert decision.specialist_name == "general_specialist"
    assert "fallback" in decision.reason.lower()
    assert decision.confidence == 0.0
    assert decision.matched_capability is None


def test_unregistered_fallback_is_rejected():
    registry = SpecialistRegistry()

    with pytest.raises(
        ValueError,
        match="Fallback specialist is not registered",
    ):
        CapabilityRouter(
            registry,
            fallback_specialist="missing_specialist",
        )
