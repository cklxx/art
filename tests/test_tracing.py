from fastapi.testclient import TestClient

from agent.infra.server import app


def test_timeline_groups_spans_by_task() -> None:
    client = TestClient(app)

    ingest_payload = {
        "texts": [
            {
                "id": "text-1",
                "content": "multimodal timeline",
                "metadata": {"source": "test"},
            }
        ],
        "images": [],
        "audio": [],
    }
    resp = client.post("/ingest/multimodal", json=ingest_payload)
    assert resp.status_code == 200

    timeline_resp = client.get("/traces/timeline", params={"task_id": "ingest"})
    assert timeline_resp.status_code == 200
    data = timeline_resp.json()
    assert isinstance(data, list)
    assert any(tl["task_id"] == "ingest" for tl in data)

    ingest_timeline = next(tl for tl in data if tl["task_id"] == "ingest")
    assert ingest_timeline["total_ms"] >= 0
    assert len(ingest_timeline["events"]) >= 1
    first_event = ingest_timeline["events"][0]
    assert "start_ms" in first_event and "duration_ms" in first_event
