"""State storage interfaces and a default in-memory implementation."""
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
