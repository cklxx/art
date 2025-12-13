"""Retrieval benchmarking helpers to keep local and external services honest."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable, List, Mapping

from pydantic import BaseModel

from .io import KnowledgeBundle
from .retrieval import RetrievalEngine, RetrievalHit


class RetrievalBenchmarkCase(BaseModel):
    """A single benchmark scenario with a corpus and a target query."""

    id: str
    bundle: KnowledgeBundle
    query: str
    relevant_ids: list[str]
    top_k: int = 5


class RetrievalBenchmarkResult(BaseModel):
    case_id: str
    hits: list[RetrievalHit]
    precision_at_k: float
    recall_at_k: float
    relevant_found: list[str]


class RetrievalBenchmarkSuite(BaseModel):
    results: list[RetrievalBenchmarkResult]
    macro_precision: float
    macro_recall: float


class AdapterBenchmarkResult(BaseModel):
    adapter: str
    suite: RetrievalBenchmarkSuite
    duration_ms: float


class AutomatedBenchmarkSummary(BaseModel):
    runs: list[AdapterBenchmarkResult]
    macro_precision: float
    macro_recall: float
    history: list[AdapterBenchmarkResult] | None = None


@dataclass
class RetrievalBenchmarkRunner:
    """Run a suite of retrieval cases against a supplied engine."""

    engine: RetrievalEngine | None = None

    def __post_init__(self) -> None:
        if self.engine is None:
            self.engine = RetrievalEngine()

    def run(self, cases: Iterable[RetrievalBenchmarkCase]) -> RetrievalBenchmarkSuite:
        per_case: List[RetrievalBenchmarkResult] = []
        for case in cases:
            assert self.engine is not None
            self.engine.reset()
            self.engine.ingest_bundle(case.bundle)
            hits = self.engine.query(case.query, top_k=case.top_k).hits
            hit_ids = [h.id for h in hits]
            relevant_found = [hid for hid in hit_ids if hid in case.relevant_ids]
            precision = round(len(relevant_found) / max(len(hits), 1), 4)
            recall = round(len(relevant_found) / max(len(case.relevant_ids), 1), 4)
            per_case.append(
                RetrievalBenchmarkResult(
                    case_id=case.id,
                    hits=hits,
                    precision_at_k=precision,
                    recall_at_k=recall,
                    relevant_found=relevant_found,
                )
            )

        macro_precision = round(
            sum(r.precision_at_k for r in per_case) / max(len(per_case), 1), 4
        )
        macro_recall = round(sum(r.recall_at_k for r in per_case) / max(len(per_case), 1), 4)

        return RetrievalBenchmarkSuite(
            results=per_case,
            macro_precision=macro_precision,
            macro_recall=macro_recall,
        )


def default_benchmark_cases() -> list[RetrievalBenchmarkCase]:
    """Provide a lightweight corpus covering text, image, and audio slices."""

    return [
        RetrievalBenchmarkCase(
            id="research-diagram",
            query="attention diagram for transformers",
            relevant_ids=["text-transformer", "image-attention"],
            top_k=3,
            bundle=KnowledgeBundle.from_texts(
                texts=[
                    {
                        "id": "text-transformer",
                        "content": "Transformer paper overview with attention diagrams and layer norms",
                        "tags": ["nlp", "attention"],
                    },
                    {
                        "id": "text-cv",
                        "content": "CNN architecture with pooling layers and feature maps",
                        "tags": ["cv"],
                    },
                ],
                images=[
                    {
                        "id": "image-attention",
                        "caption": "A heatmap showing transformer attention weights over tokens",
                        "tags": ["attention", "visualization"],
                    }
                ],
            ),
        ),
        RetrievalBenchmarkCase(
            id="speech-notes",
            query="meeting audio summary",
            relevant_ids=["audio-brief", "text-minutes"],
            top_k=3,
            bundle=KnowledgeBundle.from_texts(
                texts=[
                    {
                        "id": "text-minutes",
                        "content": "Minutes from the design review covering latency and throughput",
                        "tags": ["meeting", "summary"],
                    },
                    {
                        "id": "text-rfc",
                        "content": "RFC draft with protocol changes unrelated to meetings",
                        "tags": ["rfc"],
                    },
                ],
                audio=[
                    {
                        "id": "audio-brief",
                        "transcript": "Quick audio brief recapping the meeting takeaways and action items",
                        "tags": ["meeting", "audio"],
                    }
                ],
            ),
        ),
        RetrievalBenchmarkCase(
            id="hardware-lab",
            query="oscilloscope waveform and capacitor",
            relevant_ids=["image-scope", "text-capacitor"],
            top_k=3,
            bundle=KnowledgeBundle.from_texts(
                texts=[
                    {
                        "id": "text-capacitor",
                        "content": "Lab note describing capacitor discharge curves and RC timing",
                        "tags": ["hardware", "capacitor"],
                    },
                    {
                        "id": "text-mlp",
                        "content": "Feedforward MLP architecture for classification",
                        "tags": ["ml"],
                    },
                ],
                images=[
                    {
                        "id": "image-scope",
                        "caption": "Oscilloscope photo showing a decaying sine waveform",
                        "tags": ["hardware", "waveform"],
                    }
                ],
            ),
        ),
    ]


def default_adapter_factories() -> Mapping[str, Callable[[], RetrievalEngine]]:
    """Provide retrieval adapter flavors to compare during automation."""

    return {
        "baseline_bow": lambda: RetrievalEngine(),
        "tag_bias": lambda: RetrievalEngine(tag_boost=0.2),
        "source_bias": lambda: RetrievalEngine(source_boost=0.05),
    }


@dataclass
class AutomatedBenchmarkRunner:
    adapters: Mapping[str, Callable[[], RetrievalEngine]] | None = None
    history_limit: int = 20

    def __post_init__(self) -> None:
        self.adapters = self.adapters or default_adapter_factories()
        self._history: deque[AdapterBenchmarkResult] = deque(maxlen=self.history_limit)

    def run_all(
        self,
        cases: Iterable[RetrievalBenchmarkCase],
        adapter_names: list[str] | None = None,
        track_history: bool = True,
    ) -> AutomatedBenchmarkSummary:
        names = adapter_names or list(self.adapters.keys())
        runs: list[AdapterBenchmarkResult] = []

        for name in names:
            if name not in self.adapters:
                continue
            engine = self.adapters[name]()
            runner = RetrievalBenchmarkRunner(engine=engine)
            start = perf_counter()
            suite = runner.run(cases)
            duration_ms = round((perf_counter() - start) * 1000, 2)
            result = AdapterBenchmarkResult(
                adapter=name, suite=suite, duration_ms=duration_ms
            )
            runs.append(result)
            if track_history:
                self._history.append(result)

        macro_precision = round(
            sum(r.suite.macro_precision for r in runs) / max(len(runs), 1), 4
        )
        macro_recall = round(
            sum(r.suite.macro_recall for r in runs) / max(len(runs), 1), 4
        )

        return AutomatedBenchmarkSummary(
            runs=runs,
            macro_precision=macro_precision,
            macro_recall=macro_recall,
            history=list(self._history) if track_history else None,
        )
