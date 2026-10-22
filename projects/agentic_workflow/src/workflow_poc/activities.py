
from typing import Any

from pydantic import ValidationError
from temporalio import activity

from .models import ProtocolInput


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
    """Simulate an AI review with a predictable result."""

    return {
        "findings": [
            {
                "code": "METHOD-001",
                "description": (
                    "The protocol should clarify how missing outcome "
                    "measurements will be handled."
                ),
                "severity": "medium",
                "evidence": (
                    "The submitted protocol does not specify a "
                    "missing-outcome handling procedure."
                ),
            }
        ],
        "confidence": 0.65,
    }
