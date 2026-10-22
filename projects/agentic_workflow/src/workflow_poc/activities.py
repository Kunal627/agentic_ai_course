
from typing import Any
import os
from pydantic import ValidationError
from temporalio import activity
from openai import AsyncOpenAI
from .models import ProtocolInput, AIReviewResult
import json

def get_llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=os.getenv(
            "LLM_BASE_URL",
            "http://localhost:8080/v1",
        ),
        api_key=os.getenv("LLM_API_KEY", "not-needed"),
        timeout=60.0,
    )


@activity.defn
async def validate_protocol(
    protocol_data: dict[str, Any],
) -> dict[str, Any]:
    """Validate a complete research protocol using Pydantic."""

    try:
        protocol = ProtocolInput.model_validate(protocol_data)

        return {
            "valid": True,
            "protocol_id": protocol.protocol_id,
            "message": "Protocol passed validation.",
            "errors": [],
        }

    except ValidationError as exc:
        errors = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]

        return {
            "valid": False,
            "protocol_id": protocol_data.get("protocol_id"),
            "message": "Protocol validation failed.",
            "errors": errors,
        }



@activity.defn
async def review_protocol(
    protocol_data: dict[str, Any],
) -> dict[str, Any]:
    """Review a protocol using a local LLM."""

    client = get_llm_client()

    prompt = f"""
You are assisting with a synthetic clinical research protocol review.

Identify potential issues in the protocol's methodology, population,
inclusion and exclusion criteria, and endpoints.

Return a JSON object with exactly these top-level fields:
- findings: a list of findings
- confidence: a number between 0 and 1

Each finding must contain:
- code: short issue identifier
- description: explanation of the potential issue
- severity: one of "low", "medium", "high"
- evidence: specific evidence from the supplied protocol

If the protocol does not provide evidence for a concern, do not
invent it. Distinguish missing information from confirmed errors.
This is a preliminary review, not a clinical determination.

Protocol:
{json.dumps(protocol_data, ensure_ascii=False)}
"""
    print("[LLM CHECK] Sending request...", flush=True)
    response = await client.chat.completions.create(
        model=os.getenv(
            "LLM_MODEL",
            "Qwen3-8B-Q4_K_M.gguf",
        ),
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only valid JSON matching the requested "
                    "structure. Do not include Markdown fences."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    
    print("[LLM CHECK] Response received.", flush=True)
    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("The LLM returned an empty response.")

    try:
        result = AIReviewResult.model_validate_json(content)
    except ValidationError as exc:
        # Raise an Activity failure so Temporal's configured retry
        # policy can handle a transient malformed response.
        raise RuntimeError(
            f"The LLM returned an invalid review structure: {exc}"
        ) from exc

    return result.model_dump(mode="json")
