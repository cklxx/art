"""Memory interface definitions."""
from typing import Protocol

from ..core.state import AgentState


class Memory(Protocol):
    def load(self, state: AgentState) -> AgentState:
        ...

    def save(self, state: AgentState) -> None:
        ...
