
from agent_runtime.tools.definitions import ToolDefinition


calculator_definition = ToolDefinition(
    name="calculator.add",
    description="Add two numbers and return their sum.",
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
        "type": "number",
    },
    risk_level="low",
)

print(calculator_definition.model_dump())
print()
print(calculator_definition.model_dump_json(indent=2))
