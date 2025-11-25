"""Reward evaluation hooks."""
from ..core.state import AgentState
from .metrics import success_score


class RewardEvaluator:
    def evaluate(self, state: AgentState) -> AgentState:
        state.reward = success_score(state)
        state.scores["success"] = state.reward
        return state
