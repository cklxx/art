"""Working memory implementation placeholder."""
from ..core.state import AgentState
from .base import Memory


class WorkingMemory(Memory):
    def load(self, state: AgentState) -> AgentState:  # type: ignore[override]
        return state

    def save(self, state: AgentState) -> None:  # type: ignore[override]
        pass
