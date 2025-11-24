"""Simple reading assistant app stub."""
from ..core.agent import BaseLLMAgent
from ..core.loop import run_loop
from ..core.state import AgentState
from ..llm.judge_models import EchoJudge


def summarize_document(task_id: str, document: str) -> AgentState:
    agent = BaseLLMAgent(name="reader", llm=EchoJudge())
    state = AgentState(task_id=task_id, messages=[])
    state.messages.append({"role": "user", "content": document})  # type: ignore[arg-type]
    return run_loop(agent, state, max_steps=2)
