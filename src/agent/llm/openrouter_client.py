"""OpenRouter client implementing the ChatCompletionModel protocol.

The OpenRouter API mirrors the OpenAI chat/completions surface, so we rely on
`httpx` directly instead of adding an OpenAI dependency. The client includes a
stubbed response when no API key is provided so that unit tests and local
development can run without network access.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .base import ChatCompletionModel


class OpenRouterClient(ChatCompletionModel):
    """Minimal OpenRouter chat client with sync + async helpers."""

    def __init__(
        self,
        api_key: str | None,
        model: str = "openrouter/auto",
        base_url: str = "https://openrouter.ai/api/v1",
        referer: str | None = None,
        title: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.referer = referer
        self.title = title
        self.name = model

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-Title"] = self.title
        return headers

    def _stub_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        prompt = messages[-1]["content"] if messages else ""
        return {"content": f"[stub:{self.model}] {prompt}", "raw": None}

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        if not self.api_key:
            return self._stub_response(messages)

        payload: Dict[str, Any] = {"model": self.model, "messages": messages}
        payload.update(kwargs)

        with httpx.Client(timeout=kwargs.pop("timeout", 30.0)) as client:
            try:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                return {"content": content, "raw": data}
            except Exception:
                return self._stub_response(messages)

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        if not self.api_key:
            return self._stub_response(messages)

        payload: Dict[str, Any] = {"model": self.model, "messages": messages}
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=kwargs.pop("timeout", 30.0)) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                return {"content": content, "raw": data}
            except Exception:
                return self._stub_response(messages)
