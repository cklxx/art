from fastapi.testclient import TestClient

from agent.core.io import KnowledgeBundle, KnowledgeSlice
from agent.infra.server import app, retrieval_engine


def test_retrieval_flow_indexes_and_queries_slices():
    client = TestClient(app)
    retrieval_engine.reset()

    bundle = KnowledgeBundle(
        slices=[
            KnowledgeSlice(
                id="s1",
                summary="diagram about transformers",
                highlights=["attention mechanisms", "layer normalization"],
                modality="text",
                tags=["nlp"],
                source_refs=["paper:1"],
            ),
            KnowledgeSlice(
                id="s2",
                summary="image of a circuit diagram",
                highlights=["resistors", "capacitors"],
                modality="image",
                tags=["hardware"],
                source_refs=["lab-notes"],
            ),
        ]
    )

    index_resp = client.post("/retrieve/index", json=bundle.model_dump(mode="json"))
    assert index_resp.status_code == 200
    assert index_resp.json().get("count") == 2

    query_resp = client.post("/retrieve/query", json={"query": "diagram", "top_k": 1})
    assert query_resp.status_code == 200
    hits = query_resp.json().get("hits", [])
    assert hits
    assert hits[0]["id"] in {"s1", "s2"}
    assert hits[0]["summary"]

    retrieval_engine.reset()
