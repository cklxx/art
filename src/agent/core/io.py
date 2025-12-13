"""Multimodal I/O schemas for consistent ingestion across text, images, and audio."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, HttpUrl, field_validator


class TextDocument(BaseModel):
    """Normalized text payload."""

    id: str
    content: str
    language: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, str] = {}


class ImageDocument(BaseModel):
    """Reference to an image alongside optional captions."""

    id: str
    url: HttpUrl
    caption: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, str] = {}


class AudioDocument(BaseModel):
    """Audio payload with optional transcript for fast routing."""

    id: str
    url: HttpUrl
    transcript: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, str] = {}


class IngestionEnvelope(BaseModel):
    """Batch of multimodal documents to process together."""

    created_at: datetime = datetime.utcnow()
    texts: List[TextDocument] = []
    images: List[ImageDocument] = []
    audio: List[AudioDocument] = []

    @property
    def modalities(self) -> List[Literal["text", "image", "audio"]]:
        active = []
        if self.texts:
            active.append("text")
        if self.images:
            active.append("image")
        if self.audio:
            active.append("audio")
        return active


class KnowledgeSlice(BaseModel):
    """Normalized output used by downstream tools."""

    id: str
    summary: str
    highlights: List[str]
    modality: Literal["text", "image", "audio", "mixed"]
    source_refs: List[str] = []
    tags: List[str] = []

    @field_validator("highlights")
    @classmethod
    def ensure_highlights(cls, value: List[str]) -> List[str]:
        return [h for h in value if h]


class KnowledgeBundle(BaseModel):
    """Aggregated knowledge artifacts for a whole ingestion batch."""

    slices: List[KnowledgeSlice]
    generated_at: datetime = datetime.utcnow()
    trace_id: Optional[str] = None

    def tag(self, *tags: str) -> "KnowledgeBundle":
        for sl in self.slices:
            sl.tags = list({*sl.tags, *tags})
        return self

    @classmethod
    def from_texts(
        cls,
        *,
        texts: list[dict] | None = None,
        images: list[dict] | None = None,
        audio: list[dict] | None = None,
    ) -> "KnowledgeBundle":
        """Quickly assemble a bundle from lightweight multimodal dicts."""

        slices: List[KnowledgeSlice] = []
        for entry in texts or []:
            slices.append(
                KnowledgeSlice(
                    id=str(entry.get("id")),
                    summary=str(entry.get("content", "")),
                    highlights=[str(entry.get("content", ""))],
                    modality="text",
                    tags=list(entry.get("tags", [])),
                    source_refs=list(entry.get("sources", [])),
                )
            )

        for entry in images or []:
            slices.append(
                KnowledgeSlice(
                    id=str(entry.get("id")),
                    summary=str(entry.get("caption", "")),
                    highlights=[str(entry.get("caption", ""))],
                    modality="image",
                    tags=list(entry.get("tags", [])),
                    source_refs=list(entry.get("sources", [])),
                )
            )

        for entry in audio or []:
            slices.append(
                KnowledgeSlice(
                    id=str(entry.get("id")),
                    summary=str(entry.get("transcript", "")),
                    highlights=[str(entry.get("transcript", ""))],
                    modality="audio",
                    tags=list(entry.get("tags", [])),
                    source_refs=list(entry.get("sources", [])),
                )
            )

        return cls(slices=slices)
