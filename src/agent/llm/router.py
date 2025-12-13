"""Simple model router to dispatch chat completions."""
from typing import Dict, List

from .base import ChatCompletionModel


class LLMRouter:
    def __init__(self) -> None:
        self._models: Dict[str, ChatCompletionModel] = {}

    def register(self, role: str, model: ChatCompletionModel) -> None:
        self._models[role] = model

    def get(self, role: str) -> ChatCompletionModel:
        if role not in self._models:
            raise KeyError(f"No model registered for role '{role}'")
        return self._models[role]

    def completion(self, role: str, messages: List[Dict[str, str]], **kwargs):
        return self.get(role).completion(messages, **kwargs)
