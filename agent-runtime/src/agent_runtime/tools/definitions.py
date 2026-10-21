from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, description="The name of the tool.")
    description: str = Field(min_length=1, description="A brief description of the tool.")
    version : str = Field(min_length=1, description="The version of the tool.")

    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    risk_level: Literal["low", "medium", "high"]
    retry_safe: bool = False

    