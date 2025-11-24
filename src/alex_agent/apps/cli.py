"""Typer CLI entrypoint for demo agent loop."""
import json
import typer

from ..core.state import AgentState
from ..core.loop import run_loop
from ..core.agent import BaseLLMAgent
from ..llm.judge_models import EchoJudge
from ..eval.reward import RewardEvaluator

app = typer.Typer(help="Run demo agent tasks from the CLI")


@app.command()
def run(task_id: str, prompt: str = "Hello") -> None:
    agent = BaseLLMAgent(name="cli-agent", llm=EchoJudge(), evaluator=RewardEvaluator())
    state = AgentState(task_id=task_id, messages=[])
    state.messages.append({"role": "user", "content": prompt})  # type: ignore[arg-type]
    final_state = run_loop(agent, state, max_steps=1)
    typer.echo(json.dumps(final_state.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
