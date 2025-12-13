from fastapi.testclient import TestClient

from agent.core.io import KnowledgeBundle, KnowledgeSlice
from agent.infra.server import app


def test_orchestration_runs_retrieval_synthesis_and_evaluation():
    client = TestClient(app)
    bundle = KnowledgeBundle(
        slices=[
            KnowledgeSlice(
                id="t1",
                summary="Transformer attention primer",
                highlights=["attention weights", "layer norm"],
                modality="text",
                tags=["nlp", "attention"],
                source_refs=["paper"],
            ),
            KnowledgeSlice(
                id="i1",
                summary="Visualization of attention map",
                highlights=["attention map", "tokens"],
                modality="image",
                tags=["visualization"],
                source_refs=["diagram"],
            ),
        ]
    )

    resp = client.post(
        "/orchestrate",
        json={"goal": "attention map for transformers", "bundle": bundle.model_dump(mode="json")},
    )
    assert resp.status_code == 200
    payload = resp.json()

    assert payload["steps"]
    assert payload["evaluation"]["coverage"] >= 0
    assert len(payload["hits"]) >= 1
    assert payload["evaluation"]["passes"] in {True, False}
