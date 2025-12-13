"""Lightweight retrieval hooks and in-memory vector index for knowledge slices."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from pydantic import BaseModel

from .io import KnowledgeBundle


def _tokenize(text: str) -> List[str]:
    return [t.strip(".,;:!?()[]{}<>""'\n\t").lower() for t in text.split() if t.strip()]


def _normalize(counter: Counter[str]) -> Dict[str, float]:
    norm = math.sqrt(sum(v * v for v in counter.values())) or 1.0
    return {k: v / norm for k, v in counter.items()}


def embed_text(text: str) -> Dict[str, float]:
    """Create a simple bag-of-words embedding normalized to unit length."""

    return _normalize(Counter(_tokenize(text)))


@dataclass
class IndexedDocument:
    id: str
    vector: Dict[str, float]
    summary: str
    tags: List[str]
    modality: str
    sources: List[str]


class RetrievalHit(BaseModel):
    id: str
    score: float
    summary: str
    tags: List[str]
    modality: str
    sources: List[str] = []


class RetrievalResponse(BaseModel):
    hits: List[RetrievalHit]


class InMemoryVectorIndex:
    """A tiny, dependency-free vector index using cosine similarity."""

    def __init__(self) -> None:
        self._docs: List[IndexedDocument] = []

    def add(self, *, doc_id: str, text: str, summary: str, tags: Optional[Iterable[str]] = None, modality: str = "mixed", sources: Optional[Iterable[str]] = None) -> None:
        vector = embed_text(text)
        self._docs.append(
            IndexedDocument(
                id=doc_id,
                vector=vector,
                summary=summary,
                tags=list(tags or []),
                modality=modality,
                sources=list(sources or []),
            )
        )

    def similarity(self, query_vector: Dict[str, float], doc_vector: Dict[str, float]) -> float:
        return sum(query_vector.get(tok, 0.0) * weight for tok, weight in doc_vector.items())

    def query(self, text: str, top_k: int = 5) -> List[RetrievalHit]:
        query_vector = embed_text(text)
        scored: List[RetrievalHit] = []
        for doc in self._docs:
            score = self.similarity(query_vector, doc.vector)
            scored.append(
                RetrievalHit(
                    id=doc.id,
                    score=round(score, 4),
                    summary=doc.summary,
                    tags=doc.tags,
                    modality=doc.modality,
                    sources=doc.sources,
                )
            )
        return sorted(scored, key=lambda h: h.score, reverse=True)[:top_k]

    def reset(self) -> None:
        self._docs = []


class RetrievalEngine:
    """Index and query knowledge bundles using a lightweight vector index."""

    def __init__(
        self,
        index: Optional[InMemoryVectorIndex] = None,
        tag_boost: float = 0.0,
        source_boost: float = 0.0,
    ) -> None:
        self.index = index or InMemoryVectorIndex()
        self.tag_boost = tag_boost
        self.source_boost = source_boost

    def ingest_bundle(self, bundle: KnowledgeBundle) -> int:
        for slice_ in bundle.slices:
            text = " ".join([slice_.summary, *slice_.highlights])
            self.index.add(
                doc_id=slice_.id,
                text=text,
                summary=slice_.summary,
                tags=slice_.tags,
                modality=slice_.modality,
                sources=slice_.source_refs,
            )
        return len(bundle.slices)

    def query(self, text: str, top_k: int = 5) -> RetrievalResponse:
        query_tokens = set(_tokenize(text))
        hits = []
        for hit in self.index.query(text, top_k=top_k):
            tag_bonus = self.tag_boost * len(query_tokens.intersection(set(hit.tags)))
            source_bonus = self.source_boost if hit.sources else 0.0
            adjusted = hit.model_copy(
                update={"score": round(hit.score + tag_bonus + source_bonus, 4)}
            )
            hits.append(adjusted)
        hits = sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]
        return RetrievalResponse(hits=hits)

    def reset(self) -> None:
        self.index.reset()
