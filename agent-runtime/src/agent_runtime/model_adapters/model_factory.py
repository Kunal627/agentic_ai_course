
from typing import Any

from agent_runtime.model_adapters.base import ModelAdapter
from agent_runtime.model_adapters.openai_adapter import OpenAIAdapter


def create_model_adapter(config: dict[str, Any]) -> ModelAdapter:
    """Create a model adapter from the model configuration."""

    provider = config.get("provider", "").lower()

    if provider in {"llamacpp", "openai_compatible"}:
        return OpenAIAdapter(
            base_url=config.get(
                "base_url",
                "http://localhost:8080/v1",
            ),
            api_key=config.get("api_key", "not-needed"),
            max_tokens=config.get("max_tokens", 512),
            timeout=config.get("timeout", 120.0),
        )

    raise ValueError(
        f"Unsupported model provider: {provider!r}. "
        "Supported providers: llamacpp, openai_compatible."
    )
