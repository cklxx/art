"""Paper analysis + image review helpers."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from ..infra.config import load_settings
from ..llm.google_client import GeneratedImage, GoogleGenerativeClient


class PaperAnalysisRequest(BaseModel):
    title: str
    abstract: str
    url: str | None = None


class PaperAnalysisResponse(BaseModel):
    summary: str
    key_points: list[str]
    image_prompts: list[str]
    recommended_style: str


class ImagePrompt(BaseModel):
    id: str
    prompt: str
    style: str | None = None
    feedback: str | None = None


class ImageBatchRequest(BaseModel):
    prompts: List[ImagePrompt]
    style: str | None = None


class ImageBatchResponse(BaseModel):
    images: list[GeneratedImage]


def get_google_client() -> GoogleGenerativeClient:
    settings = load_settings()
    return GoogleGenerativeClient(
        api_key=settings.google_api_key,
        text_model=settings.google_model,
        image_model=settings.google_image_model,
    )


def analyze_paper(request: PaperAnalysisRequest, client: GoogleGenerativeClient | None = None) -> PaperAnalysisResponse:
    client = client or get_google_client()
    base_prompt = (
        f"You are an assistant summarizing research for visuals. Title: {request.title}. "
        f"Abstract: {request.abstract}. Produce 3-4 concise key points and visual hooks."
    )
    llm_result = client.completion([{ "role": "user", "content": base_prompt }])
    summary = llm_result.get("content", "") or request.abstract[:240]

    key_points = [p.strip() for p in summary.replace("-", "\n-").split("\n") if p.strip()][:4]
    if not key_points:
        key_points = [request.title, request.abstract[:120]]

    image_prompts = [
        f"Figure {idx+1}: {point}. Emphasize clarity and publication-ready style."
        for idx, point in enumerate(key_points)
    ]

    return PaperAnalysisResponse(
        summary=summary.strip(),
        key_points=key_points,
        image_prompts=image_prompts,
        recommended_style="clean journal figure with muted palette and readable labels",
    )


def generate_review_images(batch: ImageBatchRequest, client: GoogleGenerativeClient | None = None) -> ImageBatchResponse:
    client = client or get_google_client()
    prompts = [p.prompt if not p.feedback else f"{p.prompt}\nFeedback: {p.feedback}" for p in batch.prompts]
    images = client.generate_images(prompts=prompts, style=batch.style)
    return ImageBatchResponse(images=images)
