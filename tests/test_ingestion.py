from fastapi.testclient import TestClient

from agent.core.io import AudioDocument, ImageDocument, IngestionEnvelope, KnowledgeBundle, KnowledgeSlice, TextDocument
from agent.core.graphs import decision_support_graph, produce_knowledge_bundle, summarization_graph
from agent.infra.tracing import get_tracer, traced_span
from agent.eval.harness import EvaluationHarness, EvalCase
from agent.infra.server import app, create_agent


def test_ingestion_modalities_and_bundle_tags():
    envelope = IngestionEnvelope(
        texts=[TextDocument(id="t1", content="Hello")],
        images=[ImageDocument(id="i1", url="https://example.com/image.png", caption="diagram")],
        audio=[AudioDocument(id="a1", url="https://example.com/audio.mp3", transcript="hi")],
    )
    assert set(envelope.modalities) == {"text", "image", "audio"}

    bundle = KnowledgeBundle(
        slices=[
            KnowledgeSlice(id="s1", summary="summary", highlights=["h1"], modality="mixed"),
        ]
    ).tag("demo")
    assert bundle.slices[0].tags == ["demo"]


def test_graphs_produce_output():
    state = type("Obj", (), {})()

    # Summarization graph
    s_state = type("State", (), {"observation": {"key_points": ["a", "b"]}, "working_memory": {}, "done": False})()
    for step in summarization_graph():
        s_state = step(s_state)
    assert getattr(s_state, "output", "").startswith("a; b")
    assert s_state.done is True

    # Decision graph
    d_state = type("State", (), {"observation": {"options": [{"id": "x", "reason": "best"}]}, "working_memory": {}, "done": False})()
    for step in decision_support_graph():
        d_state = step(d_state)
    assert "choice=x" in getattr(d_state, "output", "")


def test_tracing_records_events():
    tracer = get_tracer()
    with traced_span("demo", foo="bar"):
        pass
    assert tracer.latest("demo") is not None


def test_eval_harness_runs_cases():
    harness = EvaluationHarness(agent_factory=create_agent, steps=1)
    cases = [EvalCase(id="1", payload={"foo": "bar"})]
    results = harness.run(cases)
    assert len(results) == 1
    assert results[0].case_id == "1"


def test_multimodal_mixer_endpoint_preserves_cues():
    client = TestClient(app)
    payload = IngestionEnvelope(
        texts=[TextDocument(id="t1", content="text cue")],
        images=[ImageDocument(id="i1", url="https://example.com/image.png", caption="image cue")],
        audio=[AudioDocument(id="a1", url="https://example.com/audio.mp3", transcript="audio cue")],
    ).model_dump(mode="json")

    response = client.post("/reason/multimodal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["slices"][0]["modality"] == "mixed"
    assert any("text:" in h for h in data["slices"][0]["highlights"])
