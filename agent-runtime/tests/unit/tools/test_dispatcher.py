
import asyncio

import pytest
import uuid
import pytest
from agent_runtime.tools.context import ToolExecutionContext

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher, ToolAttemptTimeoutError
from agent_runtime.tools.errors import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolPolicyError,
    ToolTimeoutError,
    ToolValidationError,
)
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver
from agent_runtime.tools.retry import RetryPolicy


# --------------------------------------------------
# Test tools
# --------------------------------------------------
class ContextAwareAddTool(BaseTool):
    def __init__(self):
        self.contexts: list[ToolExecutionContext] = []

    async def execute(self, arguments: dict) -> int:
        # Preserve the original BaseTool interface.
        return arguments["a"] + arguments["b"]

    async def execute_with_context(
        self,
        arguments: dict,
        context: ToolExecutionContext,
    ) -> int:
        self.contexts.append(context)
        return arguments["a"] + arguments["b"]

class FailingTimeoutTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        raise TimeoutError("Remote service timed out")
    
class AddTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        return arguments["a"] + arguments["b"]


class FailingTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        raise ValueError("Simulated permanent failure")


class InvalidOutputTool(BaseTool):
    async def execute(self, arguments: dict) -> str:
        return "not an integer"


class FlakyTool(BaseTool):
    """Fails twice, then succeeds."""

    def __init__(self):
        self.attempts = 0

    async def execute(self, arguments: dict) -> int:
        self.attempts += 1

        if self.attempts < 3:
            raise ConnectionError("Temporary failure")

        return arguments["a"] + arguments["b"]


class AlwaysFailingTool(BaseTool):
    def __init__(self):
        self.attempts = 0

    async def execute(self, arguments: dict) -> int:
        self.attempts += 1
        raise ConnectionError("Temporary failure")


class SlowTool(BaseTool):
    async def execute(self, arguments: dict) -> int:
        await asyncio.sleep(2)
        return 30


# --------------------------------------------------
# Shared test setup
# --------------------------------------------------

def make_definition(
    name: str = "calculator.add",
    *,
    retry_safe: bool = True,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description="Test tool.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        output_schema={"type": "integer"},
        risk_level="low",
        retry_safe=retry_safe,
    )


def make_dispatcher(
    tool: BaseTool,
    *,
    definition: ToolDefinition | None = None,
    allowed_tools: frozenset[str] = frozenset({"calculator.add"}),
    timeout_seconds: float = 1.0,
    overall_timeout_seconds: float = 5.0,
    retry_policy: RetryPolicy | None = None,
) -> ToolDispatcher:
    definition = definition or make_definition()

    registry = ToolRegistry()
    registry.register(definition, tool)

    return ToolDispatcher(
        ToolResolver(registry),
        ToolPolicy(allowed_tools=allowed_tools),
        timeout_seconds=timeout_seconds,
        overall_timeout_seconds=overall_timeout_seconds,
        retry_policy=retry_policy,
    )


# --------------------------------------------------
# 1. Successful execution
# --------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_success():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "success"
    assert result.attempts == 1
    assert result.tool_name == "calculator.add"
    assert result.output == 30
    assert result.error_type is None
    assert result.error_message is None
    assert result.duration_ms >= 0


# --------------------------------------------------
# 2. Input validation
# --------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_rejects_missing_required_argument():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10},
    )

    assert result.status == "error"
    assert result.error_type == "ToolValidationError"
    assert "b" in result.error_message


@pytest.mark.asyncio
async def test_dispatch_rejects_unexpected_argument():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20, "admin_override": True},
    )

    assert result.status == "error"
    assert result.error_type == "ToolValidationError"
    assert "admin_override" in result.error_message


# --------------------------------------------------
# 3. Policy and routing
# --------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_rejects_disallowed_tool():
    dispatcher = make_dispatcher(
        AddTool(),
        allowed_tools=frozenset(),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolPolicyError"


@pytest.mark.asyncio
async def test_dispatch_rejects_unknown_tool():
    dispatcher = make_dispatcher(
        AddTool(),
        allowed_tools=frozenset({"calculator.add", "calculator.other"}),
    )

    result = await dispatcher.dispatch(
        "calculator.other",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolNotFoundError"


# --------------------------------------------------
# 4. Execution errors and output validation
# --------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_normalizes_execution_exception():
    dispatcher = make_dispatcher(FailingTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolExecutionError"
    assert result.error_message


@pytest.mark.asyncio
async def test_dispatch_rejects_invalid_tool_output():
    dispatcher = make_dispatcher(InvalidOutputTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolValidationError"


# --------------------------------------------------
# 5. Retry behavior
# --------------------------------------------------

@pytest.mark.asyncio
async def test_retry_safe_tool_retries_transient_failure():
    tool = FlakyTool()

    dispatcher = make_dispatcher(
        tool,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "success"
    assert result.attempts == 3
    assert result.output == 30
    assert tool.attempts == 3


@pytest.mark.asyncio
async def test_unsafe_tool_is_not_retried():
    tool = AlwaysFailingTool()

    dispatcher = make_dispatcher(
        tool,
        definition=make_definition(retry_safe=False),
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolExecutionError"
    assert tool.attempts == 1


@pytest.mark.asyncio
async def test_non_retryable_exception_is_not_retried():
    tool = FailingTool()

    dispatcher = make_dispatcher(
        tool,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "error"
    assert result.error_type == "ToolExecutionError"


# --------------------------------------------------
# 6. Timeouts
# --------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_handles_per_attempt_timeout():
    dispatcher = make_dispatcher(
        SlowTool(),
        timeout_seconds=0.05,
        overall_timeout_seconds=1.0,
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"


@pytest.mark.asyncio
async def test_dispatch_handles_overall_deadline():
    dispatcher = make_dispatcher(
        SlowTool(),
        timeout_seconds=1.0,
        overall_timeout_seconds=0.05,
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
    )

    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"
    assert "overall" in result.error_message.lower()



@pytest.mark.asyncio
async def test_dispatch_propagates_caller_cancellation():
    dispatcher = make_dispatcher(
        SlowTool(),
        timeout_seconds=5.0,
        overall_timeout_seconds=10.0,
    )

    task = asyncio.create_task(
        dispatcher.dispatch(
            "calculator.add",
            {"a": 10, "b": 20},
        )
    )

    # Allow the dispatch coroutine to begin executing.
    await asyncio.sleep(0.05)

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task



async def test_dispatch_generates_operation_id():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    parsed_id = uuid.UUID(result.operation_id)
    assert str(parsed_id) == result.operation_id
    assert result.status == "success"


async def test_dispatch_preserves_supplied_operation_id():
    dispatcher = make_dispatcher(AddTool())
    operation_id = "op-test-001"

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
        operation_id=operation_id,
    )

    assert result.operation_id == operation_id
    assert result.status == "success"


async def test_dispatch_rejects_blank_operation_id():
    dispatcher = make_dispatcher(AddTool())

    with pytest.raises(
        ValueError,
        match="operation_id must not be empty",
    ):
        await dispatcher.dispatch(
            "calculator.add",
            {"a": 1, "b": 2},
            operation_id="   ",
        )


async def test_dispatch_passes_operation_context():
    tool = ContextAwareAddTool()
    dispatcher = make_dispatcher(tool)

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
        operation_id="op-test-001",
    )

    assert result.status == "success"
    assert result.output == 3
    assert result.operation_id == "op-test-001"
    assert result.attempts == 1

    assert len(tool.contexts) == 1
    assert tool.contexts[0].operation_id == "op-test-001"
    assert tool.contexts[0].attempt_number == 1


async def test_dispatch_generates_operation_id():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    assert result.status == "success"
    assert str(uuid.UUID(result.operation_id)) == result.operation_id


async def test_dispatch_preserves_supplied_operation_id():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
        operation_id="op-test-002",
    )

    assert result.status == "success"
    assert result.operation_id == "op-test-002"


async def test_dispatch_rejects_blank_operation_id():
    dispatcher = make_dispatcher(AddTool())

    with pytest.raises(
        ValueError,
        match="operation_id must not be empty",
    ):
        await dispatcher.dispatch(
            "calculator.add",
            {"a": 1, "b": 2},
            operation_id="   ",
        )


async def test_context_attempt_number_increments_on_retry():
    tool = ContextAwareAddTool()

    # Fail on the first attempt and succeed on the second.
    original_execute = tool.execute_with_context

    async def flaky_execute(arguments, context):
        tool.contexts.append(context)

        if context.attempt_number == 1:
            raise ConnectionError("Temporary failure")

        return await tool.execute(arguments)

    tool.execute_with_context = flaky_execute

    dispatcher = make_dispatcher(
        tool,
        definition=make_definition(retry_safe=True),
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=0,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
        operation_id="op-retry-001",
    )

    assert result.status == "success"
    assert result.output == 3
    assert result.operation_id == "op-retry-001"
    assert result.attempts == 2

    assert [c.attempt_number for c in tool.contexts] == [1, 2]
    assert all(
        c.operation_id == "op-retry-001"
        for c in tool.contexts
    )


async def test_tool_raised_timeout_error_is_not_misclassified():
    dispatcher = make_dispatcher(FailingTimeoutTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    assert result.status == "error"
    assert result.error_type == "ToolExecutionError"
    assert "TimeoutError" in result.error_message


async def test_per_attempt_timeout_returns_timeout_result():
    dispatcher = make_dispatcher(
        SlowTool(),
        timeout_seconds=0.05,
        overall_timeout_seconds=1.0,
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"
    assert result.attempts == 1


async def test_existing_tool_interface_remains_compatible():
    dispatcher = make_dispatcher(AddTool())

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 4, "b": 5},
    )

    assert result.status == "success"
    assert result.output == 9
    assert result.attempts == 1


@pytest.mark.asyncio
async def test_dispatcher_does_not_retry_cancelled_tool() -> None:
    class BlockingTool:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.cancelled = False
            self.calls = 0

        async def execute(self, arguments: dict) -> dict:
            self.calls += 1
            self.started.set()

            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise

    tool = BlockingTool()

    definition = ToolDefinition(
        name="blocking_tool",
        description="A tool used to test cancellation.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        risk_level="low",
        retry_safe=True,
    )

    registry = ToolRegistry()
    registry.register(definition, tool)

    policy = ToolPolicy(
        allowed_tools=frozenset({"blocking_tool"})
    )

    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_errors=(ConnectionError,),
        ),
    )

    task = asyncio.create_task(
        dispatcher.dispatch("blocking_tool", {})
    )

    await asyncio.wait_for(tool.started.wait(), timeout=1.0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert tool.cancelled is True
    assert tool.calls == 1

@pytest.mark.asyncio
async def test_overall_deadline_interrupts_retry_backoff():
    tool = AlwaysFailingTool()

    dispatcher = make_dispatcher(
        tool,
        timeout_seconds=1.0,
        overall_timeout_seconds=0.05,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.5,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    assert result.status == "timeout"
    assert result.error_type == "ToolTimeoutError"
    assert result.attempts == 1
    assert tool.attempts == 1

@pytest.mark.asyncio
async def test_invalid_output_is_not_retried():
    class CountingInvalidOutputTool(BaseTool):
        def __init__(self):
            self.attempts = 0

        async def execute(self, arguments: dict) -> str:
            self.attempts += 1
            return "not an integer"

    tool = CountingInvalidOutputTool()

    dispatcher = make_dispatcher(
        tool,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 1, "b": 2},
    )

    assert result.status == "error"
    assert result.error_type == "ToolValidationError"
    assert result.attempts == 1
    assert tool.attempts == 1

@pytest.mark.asyncio
async def test_dispatch_propagates_cancellation_during_retry_backoff():
    tool = AlwaysFailingTool()

    dispatcher = make_dispatcher(
        tool,
        timeout_seconds=1.0,
        overall_timeout_seconds=5.0,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=2.0,
            backoff_multiplier=2.0,
            retryable_errors=(ConnectionError,),
        ),
    )

    task = asyncio.create_task(
        dispatcher.dispatch(
            "calculator.add",
            {"a": 1, "b": 2},
        )
    )

    # Wait until the first attempt has failed and the retry delay begins.
    for _ in range(100):
        if tool.attempts == 1:
            await asyncio.sleep(0.01)
            break
        await asyncio.sleep(0.01)

    assert tool.attempts == 1

    # Cancellation should interrupt the 2-second backoff.
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    # No second execution should have started.
    assert tool.attempts == 1

class IdempotentSideEffectTool(BaseTool):
    """Test tool that performs a simulated side effect once per operation ID."""

    def __init__(self) -> None:
        self.completed_operations: dict[str, int] = {}
        self.side_effect_count = 0
        self.contexts: list[ToolExecutionContext] = []

    async def execute(self, arguments: dict) -> int:
        # The dispatcher should use execute_with_context for this tool.
        raise AssertionError("Expected execution context")

    async def execute_with_context(
        self,
        arguments: dict,
        context: ToolExecutionContext,
    ) -> int:
        self.contexts.append(context)

        # Return the stored result if this logical operation already ran.
        if context.operation_id in self.completed_operations:
            return self.completed_operations[context.operation_id]

        # Simulate a side effect and persist its result.
        self.side_effect_count += 1
        result = arguments["a"] + arguments["b"]
        self.completed_operations[context.operation_id] = result

        # Simulate losing the response after the side effect succeeded.
        if context.attempt_number == 1:
            raise ConnectionError("Simulated lost response")

        return result
    
@pytest.mark.asyncio
async def test_retry_does_not_repeat_idempotent_side_effect():
    tool = IdempotentSideEffectTool()
    operation_id = "idempotency-test-001"

    dispatcher = make_dispatcher(
        tool,
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=0,
            retryable_errors=(ConnectionError,),
        ),
    )

    result = await dispatcher.dispatch(
        "calculator.add",
        {"a": 10, "b": 20},
        operation_id=operation_id,
    )

    assert result.status == "success"
    assert result.output == 30
    assert result.operation_id == operation_id

    # The dispatcher made two attempts.
    assert result.attempts == 2

    # The simulated side effect happened only once.
    assert tool.side_effect_count == 1

    # Both attempts used the same operation ID.
    assert [c.operation_id for c in tool.contexts] == [
        operation_id,
        operation_id,
    ]

    # Each attempt has its own attempt number.
    assert [c.attempt_number for c in tool.contexts] == [1, 2]