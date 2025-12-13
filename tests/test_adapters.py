from pathlib import Path

from fastapi.testclient import TestClient

from agent.core.state import AgentState
from agent.infra.adapters import JSONLStateStore, ObjectStateStore, SQLiteStateStore
from agent.infra.server import app


def test_store_adapters_round_trip(tmp_path: Path) -> None:
    sqlite_store = SQLiteStateStore(path=tmp_path / "state.db")
    state = AgentState(task_id="abc", observation={"foo": "bar"})
    sqlite_store.save(state)
    loaded = sqlite_store.load("abc")
    assert loaded.observation["foo"] == "bar"

    json_store = JSONLStateStore(path=tmp_path / "state_log.jsonl")
    json_store.save(state)
    loaded_json = json_store.load("abc")
    assert loaded_json.task_id == "abc"

    object_store = ObjectStateStore(root=tmp_path / "objects")
    object_store.save(state)
    loaded_object = object_store.load("abc")
    assert loaded_object.observation["foo"] == "bar"


def test_adapters_endpoint_exposes_catalog() -> None:
    client = TestClient(app)
    resp = client.get("/adapters")
    assert resp.status_code == 200
    data = resp.json()
    assert any(spec["name"] == "SQLite" for spec in data.get("stores", []))
    assert any(spec["name"] == "OpenRouter" for spec in data.get("llms", []))
