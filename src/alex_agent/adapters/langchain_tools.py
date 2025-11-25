"""Adapter helpers for wrapping LangChain tools."""
from typing import Any, Dict

from ..core.tool import Tool, ToolResult


class LangChainToolAdapter:
    def __init__(self, tool) -> None:
        self.tool = tool
        self.name = getattr(tool, "name", tool.__class__.__name__)
        self.description = getattr(tool, "description", "")
        self.schema = getattr(tool, "args_schema", {})

    def __call__(self, **kwargs) -> ToolResult:  # type: ignore[override]
        output = self.tool.run(**kwargs)
        return ToolResult(name=self.name, success=True, output=output, raw=output)
