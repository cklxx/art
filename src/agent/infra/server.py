"""FastAPI server exposing the agent loop, ingestion, and paper review helpers."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.loop import run_loop
from ..core.state import AgentState
from ..core.agent import BaseLLMAgent
from ..core.graphs import (
    decision_support_graph,
    multimodal_mixer_graph,
    produce_knowledge_bundle,
    summarization_graph,
)
from ..core.io import IngestionEnvelope, KnowledgeBundle
from ..core.orchestration import (
    OrchestrationReport,
    OrchestrationRequest,
    run_orchestration,
)
from ..core.retrieval import RetrievalEngine, RetrievalResponse
from ..core.retrieval_benchmark import (
    AutomatedBenchmarkRunner,
    RetrievalBenchmarkSuite,
    RetrievalBenchmarkCase,
    RetrievalBenchmarkRunner,
    default_adapter_factories,
    default_benchmark_cases,
)
from ..infra.tracing import TraceEventPayload, TraceTimeline, get_tracer, traced_span
from ..infra.store import store_registry
from ..infra.roadmap import RoadmapStatus, get_roadmap_status
from ..infra.adapters import AdapterCatalog, bootstrap_adapters, get_adapter_catalog
from ..eval.judge_models import EchoJudge
from ..eval.harness import EvaluationHarness, EvalCase
from ..apps.paper_review import (
    ImageBatchRequest,
    ImageBatchResponse,
    PaperAnalysisRequest,
    PaperAnalysisResponse,
    analyze_paper,
    generate_review_images,
)

app = FastAPI(title="agent API", version="0.1.0")
retrieval_engine = RetrievalEngine()
automated_benchmark = AutomatedBenchmarkRunner()
bootstrap_adapters()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_agent() -> BaseLLMAgent:
    llm = EchoJudge()
    return BaseLLMAgent(name="echo", llm=llm)


def create_app() -> FastAPI:
    return app


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/roadmap", response_model=RoadmapStatus)
def roadmap() -> RoadmapStatus:
    """Expose completed work, active efforts, and the next milestones."""

    return get_roadmap_status()


@app.get("/adapters", response_model=AdapterCatalog)
def adapters() -> AdapterCatalog:
    """List available store and LLM adapters with setup guidance."""

    return get_adapter_catalog()


@app.post("/tasks/{task_id}")
def run_task(task_id: str, payload: dict) -> dict:
    agent = create_agent()
    state = AgentState(task_id=task_id, observation=payload)
    with traced_span("agent.run", task_id=task_id):
        final_state = run_loop(agent, state, max_steps=1)
    store_registry.get().save(final_state)
    return final_state.model_dump()


@app.post("/ingest/multimodal", response_model=KnowledgeBundle)
def ingest(payload: IngestionEnvelope) -> KnowledgeBundle:
    """Normalize multimodal inputs into a knowledge bundle using summarization graph."""

    agent = create_agent()
    graph = summarization_graph()
    state = AgentState(task_id="ingest", observation=payload.model_dump())
    for step in graph:
        with traced_span("graph.step", step_name=step.__name__, task_id=state.task_id):
            state = step(state)
    bundle = produce_knowledge_bundle(state)
    return bundle


@app.post("/reason/multimodal", response_model=KnowledgeBundle)
def reason_multimodal(payload: IngestionEnvelope) -> KnowledgeBundle:
    """Run the multimodal mixer graph to preserve modality-aware highlights."""

    graph = multimodal_mixer_graph()
    state = AgentState(task_id="multimodal", observation=payload.model_dump())
    for step in graph:
        with traced_span("graph.step", step_name=step.__name__, task_id=state.task_id):
            state = step(state)
    return produce_knowledge_bundle(state)


@app.post("/decide", response_model=KnowledgeBundle)
def decide(payload: dict) -> KnowledgeBundle:
    """Decision-support endpoint that returns a knowledge bundle with rationale."""

    graph = decision_support_graph()
    state = AgentState(task_id=str(payload.get("task_id", "decision")), observation=payload)
    for step in graph:
        with traced_span("graph.step", step_name=step.__name__, task_id=state.task_id):
            state = step(state)
    bundle = produce_knowledge_bundle(state)
    return bundle


@app.post("/retrieve/index")
def retrieve_index(bundle: KnowledgeBundle) -> dict:
    """Index a knowledge bundle into the lightweight retrieval engine."""

    count = retrieval_engine.ingest_bundle(bundle)
    return {"status": "indexed", "count": count}


@app.post("/retrieve/query", response_model=RetrievalResponse)
def retrieve_query(payload: dict) -> RetrievalResponse:
    """Query the retrieval engine for slices that match the supplied text."""

    query = str(payload.get("query", "")).strip()
    top_k = int(payload.get("top_k", 5))
    return retrieval_engine.query(query, top_k=top_k)


@app.post("/retrieve/benchmark", response_model=RetrievalBenchmarkSuite)
def retrieve_benchmark(payload: dict | None = None) -> RetrievalBenchmarkSuite:
    """Run a lightweight retrieval benchmark to validate adapter choices."""

    request_cases = (payload or {}).get("cases") if payload else None
    cases = (
        [RetrievalBenchmarkCase.model_validate(c) for c in request_cases]
        if request_cases
        else default_benchmark_cases()
    )
    runner = RetrievalBenchmarkRunner()
    return runner.run(cases)


@app.post("/retrieve/benchmark/automated")
def retrieve_benchmark_automated(payload: dict | None = None):
    """Run benchmarks across registered retrieval adapters and capture history."""

    payload = payload or {}
    request_cases = payload.get("cases")
    adapter_names = payload.get("adapters")
    track_history = bool(payload.get("track", True))
    cases = (
        [RetrievalBenchmarkCase.model_validate(c) for c in request_cases]
        if request_cases
        else default_benchmark_cases()
    )

    if payload.get("custom_adapters"):
        adapters = {
            name: default_adapter_factories().get(name, RetrievalEngine)
            for name in payload["custom_adapters"]
        }
        runner = AutomatedBenchmarkRunner(adapters=adapters)
    else:
        runner = automated_benchmark

    return runner.run_all(
        cases,
        adapter_names=adapter_names,
        track_history=track_history,
    )


@app.get("/traces/recent", response_model=list[TraceEventPayload])
def recent_traces(limit: int = 25) -> list[TraceEventPayload]:
    """Return recent trace events to help visualize step timings."""

    return get_tracer().export(limit=limit)


@app.get("/traces/timeline", response_model=list[TraceTimeline])
def trace_timeline(task_id: str | None = None, limit: int = 50) -> list[TraceTimeline]:
    """Replay spans grouped per task with start/end offsets for UI timelines."""

    return get_tracer().timeline(task_id=task_id, limit=limit)


@app.post("/orchestrate", response_model=OrchestrationReport)
def orchestrate(payload: OrchestrationRequest) -> OrchestrationReport:
    """Drive a multi-agent example that loops retrieval into synthesis and evaluation."""

    return run_orchestration(payload)


@app.post("/eval/run")
def run_eval(payload: dict) -> dict:
    """Execute the evaluation harness against user-supplied cases."""

    cases = [EvalCase(id=str(c["id"]), payload=c.get("payload", {})) for c in payload.get("cases", [])]
    harness = EvaluationHarness(agent_factory=create_agent)
    results = harness.run(cases)
    return {"results": [r.__dict__ for r in results]}


@app.post("/review/analyze", response_model=PaperAnalysisResponse)
def review_analyze(payload: PaperAnalysisRequest) -> PaperAnalysisResponse:
    """Analyze a paper and produce candidate image prompts."""
    return analyze_paper(payload)


@app.post("/review/images", response_model=ImageBatchResponse)
def review_images(payload: ImageBatchRequest) -> ImageBatchResponse:
    """Generate (or regenerate) review images for the supplied prompts."""
    return generate_review_images(payload)
