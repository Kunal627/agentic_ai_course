
import json
import asyncio
from agent_runtime import state
from agent_runtime.model_adapters.base import ModelAdapter
from agent_runtime.models.messages import Message
from agent_runtime.state.run_state import RunState
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.core.cost import CostEstimator



class Agent:
    """Coordinates bounded model interactions and tool execution."""

    def __init__(
        self,
        adapter: ModelAdapter,
        *,
        model: str,
        temperature: float = 0.0,
        max_steps: int = 5,
        max_total_tokens: int | None = None,
        cost_estimator: CostEstimator | None = None,
        max_cost_usd: float | None = None,
        registry: ToolRegistry | None = None,
        dispatcher: ToolDispatcher | None = None,
        policy: ToolPolicy | None = None,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        if max_total_tokens is not None and max_total_tokens < 1:
            raise ValueError("max_total_tokens must be at least 1")

        if max_cost_usd is not None and max_cost_usd < 0:
            raise ValueError("max_cost_usd cannot be negative")

        if max_cost_usd is not None and cost_estimator is None:
            raise ValueError("cost_estimator is required when max_cost_usd is configured")

        self.cost_estimator = cost_estimator
        self.max_cost_usd = max_cost_usd

        # Tool execution requires all three components.
        supplied = (
            registry is not None,
            dispatcher is not None,
            policy is not None,
        )
        if any(supplied) and not all(supplied):
            raise ValueError(
                "registry, dispatcher, and policy must be supplied together."
            )

        self.adapter = adapter
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps
        self.registry = registry
        self.dispatcher = dispatcher
        self.policy = policy
        self.max_total_tokens = max_total_tokens

    def _get_model_tools(self) -> list[dict]:
        """Build API tool schemas from registered, permitted tools."""
        if self.registry is None or self.policy is None:
            return []

        model_tools = []

        for definition in self.registry.list_definitions():
            if definition.name not in self.policy.allowed_tools:
                continue

            model_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": definition.name,
                        "description": definition.description,
                        "parameters": definition.input_schema,
                    },
                }
            )

        return model_tools


    async def _await_or_cancel(
        self,
        awaitable,
        cancellation_event: asyncio.Event | None,
    ):
        """Cancel an in-flight operation when cancellation is requested."""
        if cancellation_event is None:
            return await awaitable

        if cancellation_event.is_set():
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise asyncio.CancelledError

        operation_task = asyncio.ensure_future(awaitable)
        cancellation_task = asyncio.create_task(
            cancellation_event.wait()
        )

        try:
            done, _ = await asyncio.wait(
                {operation_task, cancellation_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if cancellation_event.is_set():
                operation_task.cancel()
                await asyncio.gather(
                    operation_task,
                    return_exceptions=True,
                )
                raise asyncio.CancelledError

            return await operation_task

        except asyncio.CancelledError:
            if not operation_task.done():
                operation_task.cancel()

            await asyncio.gather(
                operation_task,
                return_exceptions=True,
            )
            raise

        finally:
            if not cancellation_task.done():
                cancellation_task.cancel()

            await asyncio.gather(
                cancellation_task,
                return_exceptions=True,
            )


    async def run(
                self, 
                user_input: str,
                *,
                cancellation_event: asyncio.Event | None = None,) -> RunState:
        """Run the agent until completion or a configured step limit."""

        state = RunState()
        state.start()
        state.messages.append(
            Message(role="user", content=user_input)
        )

        model_tools = self._get_model_tools()

        try:
            while state.step_count < self.max_steps:
                # Ask the model to answer or request an approved tool.
                if cancellation_event is not None and cancellation_event.is_set():
                    state.cancel("Run cancelled by caller.")
                    return state
                
                if model_tools:
                    response = await self._await_or_cancel(
                        self.adapter.generate(
                            state.messages,
                            model=self.model,
                            temperature=self.temperature,
                            tools=model_tools,
                        ),
                        cancellation_event,
                    )
                else:
                    response = await self._await_or_cancel(
                        self.adapter.generate(
                            state.messages,
                            model=self.model,
                            temperature=self.temperature,
                        ),
                        cancellation_event,
                    )


                state.step_count += 1
                state.input_tokens += response.input_tokens
                state.output_tokens += response.output_tokens
                if self.cost_estimator is not None:
                    state.estimated_cost_usd += self.cost_estimator.estimate(
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                            )

                    if (self.max_cost_usd is not None
                        and state.estimated_cost_usd >= self.max_cost_usd
                        ):
                        state.fail(
                            f"Maximum estimated cost budget "
                            f"(${self.max_cost_usd:.6f}) exceeded."
                        )
                        return state

                if (
                    self.max_total_tokens is not None 
                    and state.input_tokens + state.output_tokens >= self.max_total_tokens
                    ):
                    state.fail("Maximum total token budget " f"({self.max_total_tokens}) reached.")
                    return state

                if response.finish_reason == "length":
                    state.fail(
                        "The model response was truncated because the "
                        "output token limit was reached."
                    )
                    return state

                if response.tool_calls:
                    # Preserve the assistant's tool requests in history.
                    state.messages.append(
                        Message(
                            role="assistant",
                            content=response.content,
                            tool_calls=response.tool_calls,
                        )
                    )

                    if self.dispatcher is None:
                        state.fail(
                            "The model requested tools, but tool execution "
                            "is not configured."
                        )
                        return state

                    if cancellation_event is not None and cancellation_event.is_set():
                        state.cancel("Run cancelled by caller.")
                        return state
                    
                    # Execute each requested tool through the dispatcher.
                    for tool_call in response.tool_calls:
                        if cancellation_event is not None and cancellation_event.is_set():
                            state.cancel("Run cancelled by caller.")
                            return state
                        
                        result = await self._await_or_cancel(
                            self.dispatcher.dispatch(
                                tool_call.name,
                                tool_call.arguments,
                                operation_id=tool_call.id,
                                ),
                            cancellation_event,
                            )

                        state.tool_executions.append(result)
                        # Return the outcome to the model, including
                        # normalized errors so it can respond appropriately.
                        state.messages.append(
                            Message(
                                role="tool",
                                tool_call_id=tool_call.id,
                                content=json.dumps(
                                    result.model_dump(mode="json")
                                ),
                            )
                        )

                    # Continue the loop so the model can inspect results.
                    continue

                answer = response.content or ""

                state.messages.append(
                    Message(role="assistant", content=answer)
                )
                state.complete(answer)
                return state

            state.fail(
                f"Maximum number of model interactions "
                f"({self.max_steps}) reached."
            )
            return state

        except asyncio.CancelledError:
            state.cancel("Run cancelled by caller.")
            return state

        except Exception as exc:
            state.fail(f"{type(exc).__name__}: {exc}")
            return state

