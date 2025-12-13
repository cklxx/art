from fastapi.testclient import TestClient

from agent.infra.server import app


def test_retrieval_benchmark_reports_precision_and_recall():
    client = TestClient(app)

    resp = client.post("/retrieve/benchmark", json={})
    assert resp.status_code == 200
    data = resp.json()

    assert data["macro_precision"] > 0
    assert data["macro_recall"] > 0
    assert len(data["results"]) >= 3


def test_automated_benchmark_tracks_multiple_adapters():
    client = TestClient(app)

    resp = client.post(
        "/retrieve/benchmark/automated",
        json={"adapters": ["baseline_bow", "tag_bias"]},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["macro_precision"] > 0
    assert data["macro_recall"] > 0
    assert len(data.get("runs", [])) == 2
