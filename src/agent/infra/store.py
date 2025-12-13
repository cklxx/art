"""State storage interfaces and a default in-memory implementation."""
from __future__ import annotations

from typing import Dict, Protocol

from ..core.state import AgentState


class StateStore(Protocol):
    def save(self, state: AgentState) -> None:
        ...

    def load(self, task_id: str) -> AgentState:
        ...


class InMemoryStateStore(StateStore):
    def __init__(self) -> None:
        self._states: Dict[str, AgentState] = {}

    def save(self, state: AgentState) -> None:  # type: ignore[override]
        self._states[state.task_id] = state

    def load(self, task_id: str) -> AgentState:  # type: ignore[override]
        return self._states[task_id]


class StoreRegistry:
    """Pluggable registry to swap persistence layers without code changes."""

    def __init__(self) -> None:
        self._registry: Dict[str, StateStore] = {"memory": InMemoryStateStore()}
        self.default_key = "memory"

    def register(self, key: str, store: StateStore) -> None:
        self._registry[key] = store

    def get(self, key: str | None = None) -> StateStore:
        return self._registry[key or self.default_key]


store_registry = StoreRegistry()
