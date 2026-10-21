
from abc import ABC, abstractmethod
from typing import Any

from agent_runtime.models.messages import Message, ModelResponse


class ModelAdapter(ABC):
    """Common interface for all model providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.0,
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        """Generate a response, optionally exposing available tools."""
        raise NotImplementedError
