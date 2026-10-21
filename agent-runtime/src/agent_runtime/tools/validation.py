
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from agent_runtime.tools.errors import ToolValidationError


def validate_arguments(
    arguments: dict[str, Any],
    input_schema: dict[str, Any],
) -> None:
    """Validate tool arguments against the tool's JSON Schema."""
    validator = Draft202012Validator(input_schema)

    errors = sorted(
        validator.iter_errors(arguments),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise ToolValidationError(
            f"Invalid tool arguments: {details}"
        )
