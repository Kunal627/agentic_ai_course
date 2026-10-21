
import os
import json
from pathlib import Path

from openai import AsyncOpenAI

from agent_runtime.model_adapters.base import ModelAdapter
from agent_runtime.models.messages import Message, ModelResponse, ToolCall
from typing import Any


def _sanitize_ssl_env_paths() -> None:
    """Remove invalid SSL env overrides that break HTTP clients."""

    for env_name in (
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ):
        env_value = os.environ.get(env_name)
        if not env_value:
            continue

        if not Path(env_value).exists():
            os.environ.pop(env_name, None)


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: str = "not-needed",
        max_tokens: int = 512,
        timeout: float = 120.0,
    ) -> None:
        _sanitize_ssl_env_paths()

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        self.max_tokens = max_tokens


    async def generate(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.0,
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        """Send messages and optional tool definitions to the model."""

        api_messages: list[dict[str, Any]] = []

        for message in messages:
            api_message: dict[str, Any] = {
                "role": message.role,
            }

            if message.content is not None:
                api_message["content"] = message.content

            if message.tool_call_id is not None:
                api_message["tool_call_id"] = message.tool_call_id

            if message.role == "assistant" and message.tool_calls:
                api_message["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in message.tool_calls
                ]

            api_messages.append(api_message)

        request: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**request)

        choice = response.choices[0]
        assistant_message = choice.message

        tool_calls: list[ToolCall] = []

        for call in assistant_message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Tool arguments for '{call.function.name}' "
                    "are not valid JSON."
                ) from exc

            if not isinstance(arguments, dict):
                raise ValueError(
                    f"Tool arguments for '{call.function.name}' "
                    "must be a JSON object."
                )

            tool_calls.append(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=arguments,
                )
            )

        finish_reason = choice.finish_reason
        if finish_reason not in ("stop", "tool_calls", "length"):
            finish_reason = "stop"

        return ModelResponse(
            content=assistant_message.content or None,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            input_tokens=(
                response.usage.prompt_tokens if response.usage else 0
            ),
            output_tokens=(
                response.usage.completion_tokens if response.usage else 0
            ),
        )


    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.close()
