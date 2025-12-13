"""Adapter catalog and pluggable store implementations."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal
import sqlite3

from pydantic import BaseModel

from ..core.state import AgentState
from .config import Settings, load_settings
from .store import InMemoryStateStore, StateStore, store_registry


class AdapterSpec(BaseModel):
    name: str
    kind: Literal["store", "llm"]
    status: Literal["available", "experimental", "planned", "stubbed"]
    description: str
    setup: list[str]
    example: str | None = None


class AdapterCatalog(BaseModel):
    stores: list[AdapterSpec]
    llms: list[AdapterSpec]


class SQLiteStateStore(StateStore):
    """SQLite-backed state store for lightweight persistence without external DBs."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = Path(path)
        self._db_uri = path if str(path) == ":memory:" else str(self.path)
        if self._db_uri != ":memory":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self._db_uri) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_state (
                    task_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, state: AgentState) -> None:  # type: ignore[override]
        payload = state.model_dump_json()
        with sqlite3.connect(self._db_uri) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO agent_state (task_id, payload) VALUES (?, ?)",
                (state.task_id, payload),
            )
            conn.commit()

    def load(self, task_id: str) -> AgentState:  # type: ignore[override]
        with sqlite3.connect(self._db_uri) as conn:
            cur = conn.execute("SELECT payload FROM agent_state WHERE task_id = ?", (task_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError(f"No state found for task_id={task_id}")
        return AgentState.model_validate_json(row[0])


class JSONLStateStore(StateStore):
    """Append-only JSONL store that keeps the latest copy per task in memory."""

    def __init__(self, path: str | Path = ".data/state_log.jsonl") -> None:
        self.path = Path(path)
        self._cache: Dict[str, AgentState] = {}
        self._hydrate_cache()

    def _hydrate_cache(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                state = AgentState.model_validate_json(line)
                self._cache[state.task_id] = state

    def save(self, state: AgentState) -> None:  # type: ignore[override]
        self._cache[state.task_id] = state
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fp:
            fp.write(state.model_dump_json())
            fp.write("\n")

    def load(self, task_id: str) -> AgentState:  # type: ignore[override]
        if task_id not in self._cache:
            raise KeyError(f"No state found for task_id={task_id}")
        return self._cache[task_id]


class ObjectStateStore(StateStore):
    """Simple object-store-like adapter writing per-task blobs to disk."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

    def save(self, state: AgentState) -> None:  # type: ignore[override]
        path = self._path_for(state.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json())

    def load(self, task_id: str) -> AgentState:  # type: ignore[override]
        path = self._path_for(task_id)
        if not path.exists():
            raise KeyError(f"No state found for task_id={task_id}")
        return AgentState.model_validate_json(path.read_text())


def bootstrap_adapters(settings: Settings | None = None) -> None:
    """Register known adapters into the store registry for discovery."""

    settings = settings or load_settings()
    store_registry.register("memory", InMemoryStateStore())
    store_registry.register("sqlite", SQLiteStateStore(path=settings.state_db_path))
    store_registry.register("jsonl", JSONLStateStore(path=settings.state_log_path))
    store_registry.register("object_store", ObjectStateStore(root=settings.object_store_path))


def get_adapter_catalog(settings: Settings | None = None) -> AdapterCatalog:
    settings = settings or load_settings()
    store_specs = [
        AdapterSpec(
            name="In-memory",
            kind="store",
            status="available",
            description="Volatile store ideal for dev/test; default registry target.",
            setup=["No setup required"],
            example="store_registry.get('memory').save(state)",
        ),
        AdapterSpec(
            name="SQLite",
            kind="store",
            status="available",
            description="File-backed store for lightweight persistence without external DBs.",
            setup=[f"Set STATE_DB_PATH (current: {settings.state_db_path})"],
            example="store_registry.register('sqlite', SQLiteStateStore('my_state.db'))",
        ),
        AdapterSpec(
            name="JSONL log",
            kind="store",
            status="available",
            description="Append-only JSONL log that hydrates cache on startup.",
            setup=[f"Set STATE_LOG_PATH (current: {settings.state_log_path})"],
            example="store_registry.register('jsonl', JSONLStateStore('.data/state_log.jsonl'))",
        ),
        AdapterSpec(
            name="Object store stub",
            kind="store",
            status="experimental",
            description="S3-like adapter that writes per-task blobs to a local prefix for durability tests.",
            setup=[f"Set OBJECT_STORE_PATH (current: {settings.object_store_path})"],
            example="store_registry.register('object_store', ObjectStateStore('.data/object_store'))",
        ),
        AdapterSpec(
            name="S3/Object store",
            kind="store",
            status="planned",
            description="Stream bundles to object storage for durability; sample adapter stub coming soon.",
            setup=["Provide bucket + prefix", "Implement StateStore Protocol"],
        ),
    ]

    llm_specs = [
        AdapterSpec(
            name="Local stub/echo",
            kind="llm",
            status="available",
            description="No-key echo judge suitable for offline testing and CI.",
            setup=["Default selection when no keys set"],
            example="EchoJudge via BaseLLMAgent",
        ),
        AdapterSpec(
            name="Google Gemini",
            kind="llm",
            status="available" if settings.google_api_key else "stubbed",
            description="Text + image multimodal generation through Gemini.",
            setup=["Set GOOGLE_API_KEY", f"Model: {settings.google_model}"],
            example="Set google_api_key and call GoogleGenerativeClient",
        ),
        AdapterSpec(
            name="OpenRouter",
            kind="llm",
            status="available" if settings.openrouter_api_key else "stubbed",
            description="Route to community and hosted models with a single client.",
            setup=["Set OPENROUTER_API_KEY", f"Model: {settings.openrouter_model}"],
            example="client = OpenRouterClient(settings=openrouter_settings)",
        ),
        AdapterSpec(
            name="Local/quantized",
            kind="llm",
            status="planned",
            description="Swap in local gguf/ollama runtimes via the ChatCompletionModel Protocol.",
            setup=["Point router at local endpoint"],
        ),
    ]

    return AdapterCatalog(stores=store_specs, llms=llm_specs)
