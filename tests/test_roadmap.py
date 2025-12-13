from fastapi.testclient import TestClient

from agent.infra.server import app


def test_roadmap_endpoint_exposes_status():
    client = TestClient(app)

    response = client.get("/roadmap")
    assert response.status_code == 200

    data = response.json()
    assert data.get("completed")
    assert data.get("in_progress")
    assert data.get("upcoming")
    assert data.get("technical_plan")
    assert data.get("industry_practices")
    assert data.get("optimization_focus")
    assert data.get("testing_tips")
