
from dataclasses import dataclass


@dataclass(frozen=True)
class Specialist:
    """Describes a registered specialist and its capabilities."""

    name: str
    capabilities: frozenset[str]


class SpecialistRegistry:
    """Stores specialists and resolves them by capability."""

    def __init__(self) -> None:
        self._specialists: dict[str, Specialist] = {}

    def register(self, specialist: Specialist) -> None:
        if specialist.name in self._specialists:
            raise ValueError(
                f"Specialist already registered: {specialist.name}"
            )

        if not specialist.capabilities:
            raise ValueError("A specialist must have at least one capability.")

        self._specialists[specialist.name] = specialist

    def get(self, name: str) -> Specialist | None:
        return self._specialists.get(name)

    def find_by_capability(self, capability: str) -> Specialist | None:
        matches = [
            specialist
            for specialist in self._specialists.values()
            if capability in specialist.capabilities
        ]

        if len(matches) > 1:
            raise ValueError(
                f"Multiple specialists support capability: {capability}"
            )

        return matches[0] if matches else None


    def supported_intents(self) -> frozenset[str]:
        """Return all capabilities supported by registered specialists."""
        return frozenset(
            capability
            for specialist in self._specialists.values()
            for capability in specialist.capabilities
        )
