
from agent_runtime.tools.errors import (
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolPolicyError,
)

error_types = [
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolPolicyError,
]

for error_type in error_types:
    error = error_type("Test error")
    assert isinstance(error, ToolError)
    assert str(error) == "Test error"

print("Tool error hierarchy test passed.")
