"""LangGraph runtime adapter placeholder."""
from ...core import agent as core_agent
from ...core import state as core_state


class LangGraphRuntime:
    def run(self, agent: core_agent.Agent, state: core_state.AgentState) -> core_state.AgentState:
        return agent.step(state)
