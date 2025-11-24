"""Core agent loop controller."""
from .state import AgentState
from .agent import Agent


def run_loop(agent: Agent, init_state: AgentState, max_steps: int = 8) -> AgentState:
    state = init_state
    for step in range(max_steps):
        state.step = step
        state = agent.step(state)
        if state.done:
            break
    return state
