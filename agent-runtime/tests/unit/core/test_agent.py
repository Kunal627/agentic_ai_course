
from agent_runtime.tools import execution
import pytest

from agent_runtime.core.agent import Agent
from agent_runtime.models.messages import Message, ModelResponse, ToolCall
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.dispatcher import ToolDispatcher
from agent_runtime.tools.policies import ToolPolicy
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.resolver import ToolResolver

class FakeAdapter:
    """Returns predefined model responses without calling an LLM."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def generate(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.0,
        tools: list[dict] | None = None,
    ) -> ModelResponse:
        self.calls.append(
            {
                "messages": list(messages),
                "model": model,
                "temperature": temperature,
                "tools": tools,
            }
        )

        if not self.responses:
            raise AssertionError("Unexpected model call")

        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_agent_returns_direct_answer() -> None:
    adapter = FakeAdapter(
        [
            ModelResponse(
                content="An agent uses context to choose actions.",
                finish_reason="stop",
                input_tokens=10,
                output_tokens=8,
            )
        ]
    )

    agent = Agent(adapter, model="fake-model")

    state = await agent.run("What is an AI agent?")

    assert state.status == "completed"
    assert state.final_answer == (
        "An agent uses context to choose actions."
    )
    assert state.step_count == 1
    assert state.input_tokens == 10
    assert state.output_tokens == 8
    assert len(adapter.calls) == 1


@pytest.mark.asyncio
async def test_agent_stops_at_max_steps() -> None:
    adapter = FakeAdapter(
        [
            ModelResponse(
                content="Still working",
                finish_reason="stop",
            ),
        ]
    )

    # A direct answer completes the run on the first step.
    # Use a truncated response to force a failed first step.
    adapter.responses = [
        ModelResponse(content=None, finish_reason="length"),
    ]

    agent = Agent(adapter, model="fake-model", max_steps=1)

    state = await agent.run("Do some work")

    assert state.status == "failed"
    assert state.step_count == 1
    assert "truncated" in (state.error or "").lower()


@pytest.mark.asyncio
async def test_agent_runs_tool_then_returns_final_answer() -> None:
    from agent_runtime.tools.definitions import ToolDefinition
    from agent_runtime.tools.dispatcher import ToolDispatcher
    from agent_runtime.tools.policies import ToolPolicy
    from agent_runtime.tools.registry import ToolRegistry
    from agent_runtime.tools.resolver import ToolResolver
    from agent_runtime.tools.base import BaseTool

    class AddTool(BaseTool):
        async def execute(self, arguments: dict) -> dict:
            return {"result": arguments["a"] + arguments["b"]}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="add",
            description="Add two numbers",
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
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "number"}},
                "required": ["result"],
                "additionalProperties": False,
            },
            risk_level="low",
            retry_safe=True,
        ),
        AddTool(),
    )

    policy = ToolPolicy(allowed_tools=frozenset({"add"}))
    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
    )

    adapter = FakeAdapter(
        [
            ModelResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-add-1",
                        name="add",
                        arguments={"a": 17, "b": 23},
                    )
                ],
                finish_reason="tool_calls",
            ),
            ModelResponse(
                content="17 + 23 = 40.",
                finish_reason="stop",
            ),
        ]
    )

    agent = Agent(
        adapter,
        model="fake-model",
        max_steps=3,
        registry=registry,
        dispatcher=dispatcher,
        policy=policy,
    )

    state = await agent.run("What is 17 + 23?")

    assert state.status == "completed"
    assert state.final_answer == "17 + 23 = 40."
    assert state.step_count == 2

    # The second model call should include the tool result.
    second_call_messages = adapter.calls[1]["messages"]
    tool_messages = [
        message
        for message in second_call_messages
        if message.role == "tool"
    ]

    assert len(tool_messages) == 1
    assert tool_messages[0].tool_call_id == "call-add-1"
    assert '"result": 40' in (tool_messages[0].content or "")

    # The model should have received the approved tool schema.
    assert adapter.calls[0]["tools"][0]["function"]["name"] == "add"
    assert len(state.tool_executions) == 1

    execution = state.tool_executions[0]

    assert execution.tool_name == "add"
    assert execution.operation_id == "call-add-1"
    assert execution.status == "success"
    assert execution.output == {"result": 40}
    assert execution.attempts == 1
    assert execution.duration_ms >= 0



@pytest.mark.asyncio
async def test_agent_stops_after_max_steps_with_repeated_tool_calls() -> None:
    from agent_runtime.tools.base import BaseTool
    from agent_runtime.tools.definitions import ToolDefinition
    from agent_runtime.tools.dispatcher import ToolDispatcher
    from agent_runtime.tools.policies import ToolPolicy
    from agent_runtime.tools.registry import ToolRegistry
    from agent_runtime.tools.resolver import ToolResolver

    class AddTool(BaseTool):
        async def execute(self, arguments: dict) -> dict:
            return {"result": arguments["a"] + arguments["b"]}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="add",
            description="Add two numbers",
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
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "number"}},
                "required": ["result"],
                "additionalProperties": False,
            },
            risk_level="low",
            retry_safe=True,
        ),
        AddTool(),
    )

    policy = ToolPolicy(allowed_tools=frozenset({"add"}))
    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
    )

    adapter = FakeAdapter([
        ModelResponse(
            tool_calls=[
                ToolCall(
                    id="call-1",
                    name="add",
                    arguments={"a": 1, "b": 2},
                )
            ],
            finish_reason="tool_calls",
        ),
        ModelResponse(
            tool_calls=[
                ToolCall(
                    id="call-2",
                    name="add",
                    arguments={"a": 3, "b": 4},
                )
            ],
            finish_reason="tool_calls",
        ),
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        max_steps=2,
        registry=registry,
        dispatcher=dispatcher,
        policy=policy,
    )

    state = await agent.run("Keep adding numbers.")

    assert state.status == "failed"
    assert state.step_count == 2
    assert len(adapter.calls) == 2
    assert "maximum" in (state.error or "").lower()



@pytest.mark.asyncio
async def test_agent_does_not_advertise_disallowed_tools() -> None:
    from agent_runtime.tools.base import BaseTool
    from agent_runtime.tools.definitions import ToolDefinition
    from agent_runtime.tools.dispatcher import ToolDispatcher
    from agent_runtime.tools.policies import ToolPolicy
    from agent_runtime.tools.registry import ToolRegistry
    from agent_runtime.tools.resolver import ToolResolver

    class AddTool(BaseTool):
        async def execute(self, arguments: dict) -> dict:
            return {"result": arguments["a"] + arguments["b"]}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="add",
            description="Add two numbers",
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
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "number"}},
                "required": ["result"],
                "additionalProperties": False,
            },
            risk_level="low",
            retry_safe=True,
        ),
        AddTool(),
    )

    # The tool is registered, but the policy does not allow it.
    policy = ToolPolicy(allowed_tools=frozenset())
    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
    )

    adapter = FakeAdapter([
        ModelResponse(
            content="I can answer without a tool.",
            finish_reason="stop",
        )
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        registry=registry,
        dispatcher=dispatcher,
        policy=policy,
    )

    state = await agent.run("Answer my question.")

    assert state.status == "completed"
    assert len(adapter.calls) == 1

    # No tools should be exposed to the model.
    assert adapter.calls[0]["tools"] is None


@pytest.mark.asyncio
async def test_agent_stops_when_total_token_budget_is_reached() -> None:
    adapter = FakeAdapter([
        ModelResponse(
            content="This answer uses tokens.",
            finish_reason="stop",
            input_tokens=15,
            output_tokens=10,
        ),
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        max_total_tokens=25,
    )

    state = await agent.run("Explain agents.")

    assert state.status == "failed"
    assert state.input_tokens == 15
    assert state.output_tokens == 10
    assert state.step_count == 1
    assert len(adapter.calls) == 1
    assert "token budget" in (state.error or "").lower()



@pytest.mark.asyncio
async def test_agent_cancels_before_first_model_call() -> None:
    import asyncio

    adapter = FakeAdapter([
        ModelResponse(
            content="This should never be returned.",
            finish_reason="stop",
        )
    ])

    cancellation_event = asyncio.Event()
    cancellation_event.set()

    agent = Agent(adapter, model="fake-model")

    state = await agent.run(
        "Hello",
        cancellation_event=cancellation_event,
    )

    assert state.status == "cancelled"
    assert state.step_count == 0
    assert len(adapter.calls) == 0
    assert state.completed_at is not None



@pytest.mark.asyncio
async def test_agent_cancels_in_flight_model_call() -> None:
    import asyncio

    class BlockingAdapter:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.cancelled = False

        async def generate(
            self,
            messages,
            *,
            model,
            temperature=0.0,
            tools=None,
        ):
            self.started.set()

            try:
                # Simulate a model request that never finishes normally.
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise

    adapter = BlockingAdapter()
    cancellation_event = asyncio.Event()
    agent = Agent(adapter, model="fake-model")

    run_task = asyncio.create_task(
        agent.run(
            "Wait for a response.",
            cancellation_event=cancellation_event,
        )
    )

    # Ensure the model call has actually started.
    await asyncio.wait_for(adapter.started.wait(), timeout=1.0)

    # Request cancellation while the model is still running.
    cancellation_event.set()

    state = await asyncio.wait_for(run_task, timeout=1.0)

    assert state.status == "cancelled"
    assert adapter.cancelled is True


@pytest.mark.asyncio
async def test_agent_cancels_in_flight_tool_call() -> None:
    import asyncio

    class BlockingTool:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.cancelled = False

        async def execute(self, arguments: dict) -> dict:
            self.started.set()

            try:
                # Simulate a tool that never finishes normally.
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
        output_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        risk_level="low",
        retry_safe=False,
    )

    registry = ToolRegistry()
    registry.register(definition, tool)

    policy = ToolPolicy(allowed_tools=frozenset({"blocking_tool"}))
    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
    )

    adapter = FakeAdapter([
        ModelResponse(
            finish_reason="tool_calls",
            tool_calls=[
                ToolCall(
                    id="call-1",
                    name="blocking_tool",
                    arguments={},
                )
            ],
        )
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        registry=registry,
        dispatcher=dispatcher,
        policy=policy,
    )

    cancellation_event = asyncio.Event()
    run_task = asyncio.create_task(
        agent.run("Run the blocking tool.", cancellation_event=cancellation_event)
    )

    await asyncio.wait_for(tool.started.wait(), timeout=1.0)
    cancellation_event.set()

    state = await asyncio.wait_for(run_task, timeout=1.0)

    assert state.status == "cancelled"
    assert tool.cancelled is True


@pytest.mark.asyncio
async def test_agent_tracks_estimated_model_cost() -> None:
    from agent_runtime.core.cost import CostEstimator, TokenPricing

    adapter = FakeAdapter([
        ModelResponse(
            content="Hello",
            finish_reason="stop",
            input_tokens=1_000,
            output_tokens=500,
        )
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        cost_estimator=CostEstimator(
            TokenPricing(
                input_usd_per_million=2.0,
                output_usd_per_million=8.0,
            )
        ),
    )

    state = await agent.run("Say hello")

    assert state.status == "completed"
    assert state.estimated_cost_usd == pytest.approx(0.006)


@pytest.mark.asyncio
async def test_agent_stops_when_cost_budget_is_exceeded() -> None:
    from agent_runtime.core.cost import CostEstimator, TokenPricing

    adapter = FakeAdapter([
        ModelResponse(
            content="Hello",
            finish_reason="stop",
            input_tokens=1_000,
            output_tokens=500,
        )
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        cost_estimator=CostEstimator(
            TokenPricing(
                input_usd_per_million=2.0,
                output_usd_per_million=8.0,
            )
        ),
        max_cost_usd=0.005,
    )

    state = await agent.run("Say hello")

    assert state.status == "failed"
    assert state.estimated_cost_usd == pytest.approx(0.006)
    assert "cost budget" in state.error.lower()


def test_agent_rejects_cost_budget_without_estimator() -> None:
    with pytest.raises(
        ValueError,
        match="cost_estimator is required",
    ):
        Agent(
            FakeAdapter([]),
            model="fake-model",
            max_cost_usd=0.01,
        )


def test_agent_rejects_negative_cost_budget() -> None:
    from agent_runtime.core.cost import CostEstimator, TokenPricing

    with pytest.raises(
        ValueError,
        match="max_cost_usd cannot be negative",
    ):
        Agent(
            FakeAdapter([]),
            model="fake-model",
            cost_estimator=CostEstimator(TokenPricing()),
            max_cost_usd=-0.01,
        )



@pytest.mark.asyncio
async def test_agent_does_not_execute_tool_when_token_budget_is_reached() -> None:
    from agent_runtime.tools.base import BaseTool

    class CountingTool(BaseTool):
        def __init__(self) -> None:
            self.calls = 0

        async def execute(self, arguments: dict) -> dict:
            self.calls += 1
            return {"ok": True}

    tool = CountingTool()
    definition = ToolDefinition(
        name="counting_tool",
        description="Counts executions.",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
        risk_level="low",
        retry_safe=False,
    )

    registry = ToolRegistry()
    registry.register(definition, tool)
    policy = ToolPolicy(allowed_tools=frozenset({"counting_tool"}))
    dispatcher = ToolDispatcher(
        resolver=ToolResolver(registry),
        policy=policy,
    )

    adapter = FakeAdapter([
        ModelResponse(
            tool_calls=[
                ToolCall(
                    id="call-count-1",
                    name="counting_tool",
                    arguments={},
                )
            ],
            finish_reason="tool_calls",
            input_tokens=15,
            output_tokens=10,
        )
    ])

    agent = Agent(
        adapter,
        model="fake-model",
        max_total_tokens=25,
        registry=registry,
        dispatcher=dispatcher,
        policy=policy,
    )

    state = await agent.run("Run the counting tool.")

    assert state.status == "failed"
    assert state.step_count == 1
    assert tool.calls == 0
    assert state.tool_executions == []
    assert "token budget" in (state.error or "").lower()
