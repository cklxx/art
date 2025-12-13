"""Lightweight evaluation harness for agent graphs and judges."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence

from .metrics import success_score
from .reward import RewardEvaluator
from ..core.state import AgentState
from ..core.loop import run_loop
from ..core.agent import BaseLLMAgent


@dataclass
class EvalCase:
    id: str
    payload: dict
    expected_tags: Sequence[str] | None = None


@dataclass
class EvalResult:
    case_id: str
    reward: float
    output: str | None
    tags: Sequence[str]
    passes: bool


class EvaluationHarness:
    def __init__(self, agent_factory: Callable[[], BaseLLMAgent], steps: int = 2) -> None:
        self.agent_factory = agent_factory
        self.steps = steps
        self.rewarder = RewardEvaluator()

    def run(self, cases: Iterable[EvalCase]) -> List[EvalResult]:
        results: List[EvalResult] = []
        agent = self.agent_factory()
        for case in cases:
            state = AgentState(task_id=case.id, observation=case.payload)
            final_state = run_loop(agent, state, max_steps=self.steps)
            final_state = self.rewarder.evaluate(final_state)
            tags = list(final_state.observation.get("tags", []))
            passes = success_score(final_state) > 0 and (
                not case.expected_tags or set(case.expected_tags).issubset(tags)
            )
            results.append(
                EvalResult(
                    case_id=case.id,
                    reward=final_state.reward or 0.0,
                    output=final_state.output,
                    tags=tags,
                    passes=passes,
                )
            )
        return results
