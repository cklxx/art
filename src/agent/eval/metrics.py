"""Evaluation metrics helpers."""
from ..core.state import AgentState


def count_tool_calls(state: AgentState) -> int:
    return len(state.actions)


def success_score(state: AgentState) -> float:
    return 1.0 if state.done else 0.0
