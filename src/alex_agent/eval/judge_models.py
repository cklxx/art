"""Placeholder judge model wrappers."""
from typing import Any, Dict, List

from ..llm.base import ChatCompletionModel


class EchoJudge(ChatCompletionModel):
    name = "echo-judge"

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        return {"content": "ok", "scores": {"echo": 1.0}}

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        return self.completion(messages, **kwargs)
