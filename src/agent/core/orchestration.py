"""Multi-agent orchestration demo that keeps retrieval and evaluation in the loop."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from .io import KnowledgeBundle, KnowledgeSlice
from .retrieval import RetrievalEngine, RetrievalHit


class OrchestrationRequest(BaseModel):
    goal: str
    bundle: KnowledgeBundle
    top_k: int = 3


class OrchestrationStep(BaseModel):
    name: str
    summary: str
    notes: dict | None = None


class OrchestrationReport(BaseModel):
    hits: List[RetrievalHit]
    synthesis: KnowledgeBundle
    evaluation: dict
    steps: List[OrchestrationStep]


def run_orchestration(request: OrchestrationRequest) -> OrchestrationReport:
    """Drive a two-agent flow: retrieve → synthesize → evaluate coverage."""

    retrieval = RetrievalEngine()
    retrieval.ingest_bundle(request.bundle)
    hits = retrieval.query(request.goal, top_k=request.top_k).hits

    steps: List[OrchestrationStep] = [
        OrchestrationStep(
            name="retrieval",
            summary=f"Found {len(hits)} hits for goal '{request.goal}'",
            notes={"ids": [h.id for h in hits]},
        )
    ]

    highlight_texts = [h.summary for h in hits if h.summary]
    merged_summary = " ".join(highlight_texts) or "No supporting context found"
    synthesis_bundle = KnowledgeBundle(
        slices=[
            KnowledgeSlice(
                id="synthesis",
                summary=merged_summary,
                highlights=highlight_texts,
                modality="mixed",
                tags=sorted({tag for hit in hits for tag in hit.tags}),
                source_refs=[ref for hit in hits for ref in hit.sources],
            )
        ]
    )
    steps.append(
        OrchestrationStep(
            name="synthesis",
            summary="Consolidated retrieval hits into a single bundle for downstream agents.",
            notes={"tags": synthesis_bundle.slices[0].tags},
        )
    )

    coverage = _coverage_score(request.goal, hits)
    avg_relevance = round(sum(h.score for h in hits) / max(len(hits), 1), 4)
    evaluation = {
        "coverage": coverage,
        "avg_relevance": avg_relevance,
        "passes": coverage >= 0.5,
    }
    steps.append(
        OrchestrationStep(
            name="evaluation",
            summary="Measured how well retrieval results cover the goal keywords.",
            notes=evaluation,
        )
    )

    return OrchestrationReport(
        hits=hits,
        synthesis=synthesis_bundle,
        evaluation=evaluation,
        steps=steps,
    )


def _coverage_score(goal: str, hits: List[RetrievalHit]) -> float:
    terms = {t.lower() for t in goal.split() if len(t) > 3}
    if not terms:
        return 0.0
    found: set[str] = set()
    for hit in hits:
        text = " ".join([hit.summary, *hit.tags])
        lower_text = text.lower()
        found.update({t for t in terms if t in lower_text})
    return round(len(found) / len(terms), 4)
