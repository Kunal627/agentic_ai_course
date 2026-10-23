
import pytest

from routing.registry import Specialist, SpecialistRegistry


def test_register_and_retrieve_specialist():
    registry = SpecialistRegistry()
    specialist = Specialist(
        name="protocol_specialist",
        capabilities=frozenset({"protocol_review"}),
    )

    registry.register(specialist)

    assert registry.get("protocol_specialist") == specialist


def test_find_specialist_by_capability():
    registry = SpecialistRegistry()
    specialist = Specialist(
        name="eligibility_specialist",
        capabilities=frozenset({"eligibility_evaluation"}),
    )
    registry.register(specialist)

    result = registry.find_by_capability("eligibility_evaluation")

    assert result == specialist


def test_unknown_capability_returns_none():
    registry = SpecialistRegistry()

    assert registry.find_by_capability("unknown_intent") is None


def test_duplicate_specialist_is_rejected():
    registry = SpecialistRegistry()
    specialist = Specialist(
        name="protocol_specialist",
        capabilities=frozenset({"protocol_review"}),
    )
    registry.register(specialist)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(specialist)


def test_duplicate_capability_is_rejected_during_lookup():
    registry = SpecialistRegistry()
    registry.register(
        Specialist(
            name="protocol_specialist",
            capabilities=frozenset({"protocol_review"}),
        )
    )
    registry.register(
        Specialist(
            name="backup_protocol_specialist",
            capabilities=frozenset({"protocol_review"}),
        )
    )

    with pytest.raises(ValueError, match="Multiple specialists"):
        registry.find_by_capability("protocol_review")


def test_supported_intents_returns_all_registered_capabilities():
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

    assert registry.supported_intents() == frozenset({
        "protocol_review",
        "eligibility_evaluation",
    })
