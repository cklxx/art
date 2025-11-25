"""Agent interfaces and base implementations."""
from typing import Protocol, Sequence

from .state import AgentState, AgentMessage
from .tool import Tool
from ..memory.policy import MemoryPolicy
from ..eval.reward import RewardEvaluator


class Agent(Protocol):
    name: str

    def step(self, state: AgentState) -> AgentState:
        ...


class BaseLLMAgent:
    """Minimal LLM agent skeleton to plug in custom tools and memory policies."""

    def __init__(
        self,
        name: str,
        llm,
        tools: Sequence[Tool] | None = None,
        memory_policy: MemoryPolicy | None = None,
        evaluator: RewardEvaluator | None = None,
    ) -> None:
        self.name = name
        self.llm = llm
        self.tools = list(tools or [])
        self.memory_policy = memory_policy
        self.evaluator = evaluator

    def step(self, state: AgentState) -> AgentState:
        # 1. Apply memory policy to enrich state
        if self.memory_policy:
            state = self.memory_policy.apply(state)

        # 2. Compose messages for the LLM
        messages = [m.model_dump(exclude_none=True) for m in state.messages]
        llm_response = self.llm.completion(messages)

        # 3. Optionally call tools
        for tool in self.tools:
            if tool.name in llm_response.get("tools", {}):
                result = tool(**llm_response["tools"][tool.name])
                state.actions.append(result.model_dump())
                state.observation[tool.name] = result.output

        # 4. Update messages with LLM output
        content = llm_response.get("content", "")
        state.messages.append(AgentMessage(role="assistant", content=content))
        state.output = content

        # 5. Evaluate
        if self.evaluator:
            state = self.evaluator.evaluate(state)

        # 6. Decide completion
        state.done = llm_response.get("done", False)
        return state
