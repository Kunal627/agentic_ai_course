
from agent_runtime.tools.errors import ToolValidationError
from agent_runtime.tools.validation import validate_arguments

schema = {
    "type": "object",
    "properties": {
        "a": {"type": "number"},
        "b": {"type": "number"},
    },
    "required": ["a", "b"],
    "additionalProperties": False,
}

# Valid arguments should pass.
validate_arguments({"a": 10, "b": 20}, schema)
print("Valid arguments accepted.")

# Invalid arguments should raise our normalized validation error.
invalid_cases = [
    {"a": 10},                          # Missing b
    {"a": 10, "b": 20, "c": 30},       # Extra property
    {"a": "hello", "b": 20},           # Wrong type
]

for arguments in invalid_cases:
    try:
        validate_arguments(arguments, schema)
    except ToolValidationError as exc:
        print(f"Invalid arguments rejected: {exc}")
    else:
        raise AssertionError(
            f"Invalid arguments were accepted: {arguments}"
        )

print("Tool validation test passed.")
