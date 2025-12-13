"""Qwen client wrapper implementing ChatCompletionModel."""
from typing import Any, Dict, List

from .base import ChatCompletionModel

try:
    from dashscope import Generation
except ImportError:  # pragma: no cover - optional dependency
    Generation = None


class QwenClient(ChatCompletionModel):
    def __init__(self, model: str = "qwen-plus") -> None:
        if Generation is None:
            raise ImportError("dashscope package is required for QwenClient")
        self.model = model
        self.name = model

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        response = Generation.call(model=self.model, messages=messages, **kwargs)
        return {"content": response.output.choices[0].message["content"], "raw": response}

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        return self.completion(messages, **kwargs)
