
class ToolError(Exception):
    """Base exception for tool-related failures."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not registered."""


class ToolValidationError(ToolError):
    """Raised when tool arguments or results are invalid."""


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds its deadline."""


class ToolPolicyError(ToolError):
    """Raised when a tool call violates an execution policy."""
