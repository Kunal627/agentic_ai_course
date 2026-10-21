
import asyncio
import time
from typing import Any, Callable
from uuid import uuid4

from jsonschema import Draft202012Validator

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.context import ToolExecutionContext
from agent_runtime.tools.errors import (
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
)
from agent_runtime.tools.execution import ToolExecutionResult
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.resolver import ToolResolver
from agent_runtime.tools.retry import RetryPolicy
from agent_runtime.tools.validation import validate_arguments


class ToolAttemptTimeoutError(Exception):
    """A tool execution exceeded its per-attempt timeout."""


class ToolDispatcher:
    """Coordinates policy checks, validation, retries, and execution."""

    def __init__(
        self,
        resolver: ToolResolver,
        policy: ToolPolicy,
        *,
        timeout_seconds: float = 10.0,
        overall_timeout_seconds: float = 30.0,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        if overall_timeout_seconds <= 0:
            raise ValueError(
                "overall_timeout_seconds must be greater than zero"
            )

        self._resolver = resolver
        self._policy = policy
        self._timeout_seconds = timeout_seconds
        self._overall_timeout_seconds = overall_timeout_seconds
        self._retry_policy = retry_policy or RetryPolicy()

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        operation_id: str | None = None,
    ) -> ToolExecutionResult:
        """Execute one logical tool operation within an overall deadline."""
        if operation_id is None:
            operation_id = str(uuid4())
        elif not operation_id.strip():
            raise ValueError("operation_id must not be empty")

        start_time = time.perf_counter()
        attempts = 0

        def record_attempt() -> None:
            nonlocal attempts
            attempts += 1

        deadline = asyncio.timeout(self._overall_timeout_seconds)

        try:
            async with deadline:
                # Resolve and authorize the requested tool.
                resolved = self._resolver.resolve(tool_name)
                self._policy.check(tool_name)

                # Validate arguments before executing the tool.
                validate_arguments(
                    arguments,
                    resolved.definition.input_schema,
                )

                # Execute, retrying only when policy permits.
                output = await self._execute_with_retries(
                    resolved.implementation,
                    arguments,
                    operation_id=operation_id,
                    retry_safe=resolved.definition.retry_safe,
                    record_attempt=record_attempt,
                )

                # Validate the returned output.
                output_validator = Draft202012Validator(
                    resolved.definition.output_schema
                )
                output_errors = list(output_validator.iter_errors(output))

                if output_errors:
                    details = "; ".join(
                        error.message for error in output_errors
                    )
                    raise ToolValidationError(
                        f"Invalid output from tool '{tool_name}': {details}"
                    )

                return ToolExecutionResult(
                    tool_name=tool_name,
                    operation_id=operation_id,
                    status="success",
                    output=output,
                    attempts=attempts,
                    duration_ms=(
                        time.perf_counter() - start_time
                    ) * 1000,
                )

        except TimeoutError as exc:
            if deadline.expired():
                return ToolExecutionResult(
                    tool_name=tool_name,
                    operation_id=operation_id,
                    status="timeout",
                    error_type="ToolTimeoutError",
                    error_message=(
                        "Tool execution exceeded the overall timeout "
                        f"of {self._overall_timeout_seconds} seconds."
                    ),
                    attempts=attempts,
                    duration_ms=(
                        time.perf_counter() - start_time
                    ) * 1000,
                )

            # The tool itself raised TimeoutError, rather than the
            # dispatcher's overall timeout expiring.
            return self._error_result(
                tool_name,
                operation_id,
                "ToolExecutionError",
                f"{type(exc).__name__}: {exc}",
                start_time,
                attempts,
            )

        except ToolAttemptTimeoutError as exc:
            return ToolExecutionResult(
                tool_name=tool_name,
                operation_id=operation_id,
                status="timeout",
                error_type="ToolTimeoutError",
                error_message=str(exc),
                attempts=attempts,
                duration_ms=(
                    time.perf_counter() - start_time
                ) * 1000,
            )

        except ToolNotFoundError as exc:
            return self._error_result(
                tool_name,
                operation_id,
                "ToolNotFoundError",
                str(exc),
                start_time,
                attempts,
            )

        except ToolValidationError as exc:
            return self._error_result(
                tool_name,
                operation_id,
                "ToolValidationError",
                str(exc),
                start_time,
                attempts,
            )

        except ToolError as exc:
            return self._error_result(
                tool_name,
                operation_id,
                type(exc).__name__,
                str(exc),
                start_time,
                attempts,
            )

        except Exception as exc:
            return self._error_result(
                tool_name,
                operation_id,
                "ToolExecutionError",
                f"{type(exc).__name__}: {exc}",
                start_time,
                attempts,
            )

    @staticmethod
    def _error_result(
        tool_name: str,
        operation_id: str,
        error_type: str,
        error_message: str,
        start_time: float,
        attempts: int,
    ) -> ToolExecutionResult:
        """Build a normalized error result."""
        return ToolExecutionResult(
            tool_name=tool_name,
            operation_id=operation_id,
            status="error",
            error_type=error_type,
            error_message=error_message,
            attempts=attempts,
            duration_ms=(
                time.perf_counter() - start_time
            ) * 1000,
        )

    async def _execute_with_retries(
        self,
        tool: BaseTool,
        arguments: dict[str, Any],
        *,
        operation_id: str,
        retry_safe: bool,
        record_attempt: Callable[[], None],
    ) -> Any:
        """Execute a tool with bounded attempts and execution context."""
        retry_policy = self._retry_policy

        for attempt_number in range(
            1, retry_policy.max_attempts + 1
        ):
            record_attempt()

            context = ToolExecutionContext(
                operation_id=operation_id,
                attempt_number=attempt_number,
            )

            try:
                timeout_scope = asyncio.timeout(
                    self._timeout_seconds
                )

                try:
                    async with timeout_scope:
                        execute_with_context = getattr(
                            tool,
                            "execute_with_context",
                            None,
                        )

                        if callable(execute_with_context):
                            return await execute_with_context(
                                arguments,
                                context,
                            )

                        # Backward compatibility with existing tools.
                        return await tool.execute(arguments)

                except TimeoutError as exc:
                    if timeout_scope.expired():
                        raise ToolAttemptTimeoutError(
                            "Tool execution exceeded the per-attempt "
                            f"timeout of {self._timeout_seconds} seconds."
                        ) from exc

                    # A TimeoutError originated inside the tool.
                    raise

            except Exception as exc:
                if not retry_safe:
                    raise

                if not retry_policy.should_retry(
                    exc, attempt_number
                ):
                    raise

                delay = retry_policy.delay_for_retry(attempt_number)
                await asyncio.sleep(delay)

        raise RuntimeError("Retry loop exited unexpectedly.")
