from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base interface for registered tools."""

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool with the given arguments."""
        raise NotImplementedError