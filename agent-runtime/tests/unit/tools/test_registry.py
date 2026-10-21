
import pytest

from agent_runtime.tools.base import BaseTool
from agent_runtime.tools.definitions import ToolDefinition
from agent_runtime.tools.registry import ToolRegistry


class DummyTool(BaseTool):
    async def execute(self, arguments: dict) -> str:
        return "ok"


def make_definition(name: str = "calculator.add") -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description=f"Test tool: {name}",
        version="1.0.0",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={"type": "string"},
        risk_level="low",
    )


def test_register_and_get_tool():
    registry = ToolRegistry()
    definition = make_definition()
    tool = DummyTool()

    registry.register(definition, tool)

    assert registry.get_tool("calculator.add") is tool


def test_register_and_get_definition():
    registry = ToolRegistry()
    definition = make_definition()

    registry.register(definition, DummyTool())

    retrieved = registry.get_definition("calculator.add")

    assert retrieved is definition
    assert retrieved.name == "calculator.add"
    assert retrieved.version == "1.0.0"


def test_duplicate_registration_is_rejected():
    registry = ToolRegistry()

    registry.register(make_definition(), DummyTool())

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(make_definition(), DummyTool())


def test_unknown_tool_lookup_raises_key_error():
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="not registered"):
        registry.get_tool("unknown.tool")

    with pytest.raises(KeyError, match="not registered"):
        registry.get_definition("unknown.tool")


def test_list_definitions_returns_registered_definitions():
    registry = ToolRegistry()
    first = make_definition("calculator.add")
    second = make_definition("calculator.subtract")

    registry.register(first, DummyTool())
    registry.register(second, DummyTool())

    definitions = registry.list_definitions()

    assert len(definitions) == 2
    assert definitions == [first, second]
    assert {definition.name for definition in definitions} == {
        "calculator.add",
        "calculator.subtract",
    }


def test_list_definitions_returns_empty_list_initially():
    registry = ToolRegistry()

    assert registry.list_definitions() == []
