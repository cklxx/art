"""Memory policy for selecting what to persist and load."""
from ..core.state import AgentState
from .base import Memory


class MemoryPolicy:
    def __init__(self, working: Memory | None = None, session: Memory | None = None, long_term: Memory | None = None):
        self.working = working
        self.session = session
        self.long_term = long_term

    def apply(self, state: AgentState) -> AgentState:
        if self.session:
            state = self.session.load(state)
        if self.long_term:
            state = self.long_term.load(state)
        if self.working:
            state = self.working.load(state)
        return state

    def persist(self, state: AgentState) -> None:
        if self.working:
            self.working.save(state)
        if self.session:
            self.session.save(state)
        if self.long_term:
            self.long_term.save(state)
