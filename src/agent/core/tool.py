"""Tool abstraction for agents."""
from typing import Any, Dict, Protocol
from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]


class ToolResult(BaseModel):
    name: str
    success: bool
    output: Any
    raw: Any = None


class Tool(Protocol):
    name: str
    description: str
    schema: dict

    def __call__(self, **kwargs) -> ToolResult:
        ...
