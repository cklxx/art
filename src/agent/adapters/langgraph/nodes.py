"""LangGraph node definitions placeholder."""
from ...core.state import AgentState


def agent_node(agent, state: AgentState) -> AgentState:
    return agent.step(state)
