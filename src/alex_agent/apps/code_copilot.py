"""Example app wiring planner/solver pattern."""
from ..core.agent import BaseLLMAgent
from ..core.loop import run_loop
from ..core.state import AgentState
from ..eval.reward import RewardEvaluator
from ..eval.judge_models import EchoJudge


def run_code_copilot(task_id: str, prompt: str) -> AgentState:
    agent = BaseLLMAgent(name="code-copilot", llm=EchoJudge(), evaluator=RewardEvaluator())
    state = AgentState(task_id=task_id, messages=[])
    state.messages.append({"role": "user", "content": prompt})  # type: ignore[arg-type]
    return run_loop(agent, state)
