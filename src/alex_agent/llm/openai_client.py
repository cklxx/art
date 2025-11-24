"""OpenAI client wrapper implementing ChatCompletionModel."""
from typing import Any, Dict, List

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None

from .base import ChatCompletionModel


class OpenAIClient(ChatCompletionModel):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        if OpenAI is None:
            raise ImportError("openai package is required for OpenAIClient")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.name = model

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        response = self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return {"content": response.choices[0].message.content, "raw": response}

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        response = await self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return {"content": response.choices[0].message.content, "raw": response}
