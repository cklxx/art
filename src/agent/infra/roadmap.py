"""Centralized roadmap status and planning helpers."""
from __future__ import annotations

from pydantic import BaseModel


class RoadmapStatus(BaseModel):
    completed: list[str]
    in_progress: list[str]
    upcoming: list[str]
    technical_plan: list[str]
    risks: list[str]
    industry_practices: list[str]
    optimization_focus: list[str]
    testing_tips: list[str]


def get_roadmap_status() -> RoadmapStatus:
    """Return a structured view of what is done and what comes next."""

    completed = [
        "Agent rename finalized with consistent entrypoints and packaging.",
        "Multimodal ingestion schemas (text/image/audio) with knowledge bundle helpers.",
        "Summarization + decision-support graphs wired through FastAPI endpoints.",
        "In-memory tracing, evaluation harness, and state-store registry for adapters.",
        "Lightweight retrieval hooks for knowledge bundles with indexing + query endpoints.",
        "Multimodal mixer graph to keep text/image/audio cues aligned per step.",
        "Adapter catalog with SQLite/JSONL samples plus FastAPI surface for discovery.",
        "Frontend observability panel surfacing roadmap data, adapters, traces, and retrieval queries.",
        "Object-store stub adapter for durability drills without external services.",
        "Trace timeline endpoint for replaying grouped spans in the UI.",
        "Retrieval benchmark runner with canned multimodal corpora to compare adapter choices.",
        "Multi-agent orchestration path that loops retrieval into synthesis and evaluation.",
        "Automated retrieval benchmark trends across adapter flavors to track precision/recall drift.",
        "Frontend orchestration replay with custom goal/context inputs and evaluation readout.",
    ]

    in_progress = [
        "Promote the object-store stub into an S3-compatible adapter with signed URL support.",
        "Add local/quantized LLM runtime adapters and model-selection router hooks.",
    ]

    upcoming = [
        "Deepen trace/bundle replay UX with richer retrieval/orchestration visualizations.",
    ]

    technical_plan = [
        "Keep the FastAPI layer thin and wire agents/graphs through dependency-injected factories.",
        "Use the `StoreRegistry` to register optional persistence backends (vector DBs, S3, or SQLite) while defaulting to memory.",
        "Prefer pluggable LLM clients (Google, OpenRouter, local) and guard them with stubbed fallbacks to stay keyless by default.",
        "Keep evaluation lightweight via the `EvaluationHarness` so new judges or reward models can be swapped in quickly.",
    ]

    risks = [
        "Model coverage depends on available free/community tiers and may vary by region.",
        "Vector retrieval remains lightweight; production deployments should swap in hardened services.",
        "Multimodal inputs can hide safety issues without upfront filtering (PII, NSFW).",
    ]

    industry_practices = [
        "Align modalities early with shared embeddings or cross-attention so downstream graphs can fuse signals consistently.",
        "Preserve modality tags through the pipeline (ingestion → retrieval → reasoning) to avoid losing provenance and weighting cues.",
        "Lean on retrieval-augmented prompting with contrastive negatives to keep generations grounded in ingested context.",
        "Track per-modality quality metrics (caption fidelity, OCR accuracy, audio ASR confidence) before mixing outputs.",
        "Favor lightweight safety/guardrail passes (NSFW, PII, toxicity) prior to storing or surfacing multimodal results.",
    ]

    optimization_focus = [
        "Swap stubbed LLM clients with free/community tiers first (e.g., Gemini free, OpenRouter promos) before paid routing.",
        "Cache cross-modal embeddings locally and reuse them in retrieval to minimize repeated encoding costs.",
        "Benchmark the built-in retrieval engine against small vector DBs (Chroma, SQLite FTS) to choose a portable default.",
        "Instrument graph steps with tracing spans and capture bundle-level stats to surface slow or lossy stages in the UI.",
    ]

    testing_tips = [
        "Use Google AI Studio's Gemini free tier (`GOOGLE_API_KEY`) for text and image calls; defaults stub when unset.",
        "OpenRouter offers community-hosted models and occasional free-tier slots—sign up for an API key and pick a free/low-cost model.",
        "For local/offline checks, rely on the built-in stub responses (no keys required) and run `python -m pytest` for quick validation.",
    ]

    return RoadmapStatus(
        completed=completed,
        in_progress=in_progress,
        upcoming=upcoming,
        technical_plan=technical_plan,
        risks=risks,
        industry_practices=industry_practices,
        optimization_focus=optimization_focus,
        testing_tips=testing_tips,
    )
