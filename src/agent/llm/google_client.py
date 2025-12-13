"""Google Generative AI client for text + image generation."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from urllib.parse import quote_plus

import google.generativeai as genai
from pydantic import BaseModel

from .base import ChatCompletionModel


class GeneratedImage(BaseModel):
    """Normalized image generation result."""

    prompt: str
    url: str
    provider: str = "google"
    note: str | None = None


class GoogleGenerativeClient(ChatCompletionModel):
    name: str = "google-genai"

    def __init__(self, api_key: str | None, text_model: str, image_model: str):
        self.api_key = api_key
        self.text_model = text_model
        self.image_model = image_model
        if api_key:
            genai.configure(api_key=api_key)

    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        return await asyncio.to_thread(self.completion, messages, **kwargs)

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        prompt = messages[-1]["content"] if messages else ""
        if not self.api_key:
            return {"content": f"[stub:{self.text_model}] {prompt}"}

        try:
            model = genai.GenerativeModel(self.text_model)
            response = model.generate_content(prompt)
            return {"content": response.text or ""}
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {"content": f"[fallback:{type(exc).__name__}] {prompt}"}

    def generate_images(self, prompts: List[str], style: str | None = None) -> List[GeneratedImage]:
        """Generate images for prompts, falling back to placeholders if the API is unavailable."""
        results: list[GeneratedImage] = []

        if not prompts:
            return results

        if not self.api_key:
            for prompt in prompts:
                safe_text = quote_plus(prompt[:60] or "image")
                results.append(
                    GeneratedImage(
                        prompt=prompt,
                        url=f"https://placehold.co/1024x1024?text={safe_text}",
                        note="stub: set GOOGLE_API_KEY to use real images",
                    )
                )
            return results

        for prompt in prompts:
            composed_prompt = f"{prompt}\n\nStyle: {style}" if style else prompt
            try:
                model = genai.GenerativeModel(self.image_model)
                response = model.generate_images(prompt=composed_prompt)
                # The SDK returns base64 objects; expose the first image as a data URL for simplicity.
                if hasattr(response, "generated_images") and response.generated_images:
                    image = response.generated_images[0]
                    data = getattr(image, "data", None)
                    if data:
                        results.append(
                            GeneratedImage(
                                prompt=prompt,
                                url=f"data:image/png;base64,{data}",
                                note="google-genai",
                            )
                        )
                        continue
                # Fallback if the structure is different
                results.append(
                    GeneratedImage(
                        prompt=prompt,
                        url=f"https://placehold.co/1024x1024?text={quote_plus(prompt[:60])}",
                        note="unexpected_response",
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive fallback
                results.append(
                    GeneratedImage(
                        prompt=prompt,
                        url=f"https://placehold.co/1024x1024?text={quote_plus(prompt[:60])}",
                        note=f"error:{type(exc).__name__}",
                    )
                )
        return results
