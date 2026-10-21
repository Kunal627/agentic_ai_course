
from agent_runtime.tools.execution import ToolExecutionResult

success = ToolExecutionResult(
    tool_name="calculator.add",
    operation_id="op-test-success",
    status="success",
    output=30,
    duration_ms=1.25,
)

failure = ToolExecutionResult(
    tool_name="calculator.add",
    operation_id="op-test-failure",
    status="error",
    error_type="ToolExecutionError",
    error_message="Calculation failed.",
    duration_ms=2.5,
)

timeout = ToolExecutionResult(
    tool_name="calculator.add",
    operation_id="op-test-timeout",
    status="timeout",
    error_type="ToolTimeoutError",
    error_message="Execution exceeded its deadline.",
    duration_ms=1000.0,
)

assert success.output == 30
assert success.status == "success"
assert failure.error_type == "ToolExecutionError"
assert timeout.status == "timeout"

print("Tool execution result tests passed.")
print(success.model_dump())
