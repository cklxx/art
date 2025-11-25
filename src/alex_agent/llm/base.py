"""LLM interface definitions."""
from typing import Any, Dict, List, Protocol


class ChatCompletionModel(Protocol):
    name: str

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        ...

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        ...
