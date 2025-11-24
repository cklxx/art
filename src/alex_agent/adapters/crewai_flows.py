"""CrewAI flow adapter placeholder."""
from ..core.agent import BaseLLMAgent
from ..core.state import AgentState


class CrewAIAgent(BaseLLMAgent):
    def __init__(self, crew_flow, name: str = "crewai-flow"):
        super().__init__(name=name, llm=crew_flow)
        self.crew_flow = crew_flow

    def step(self, state: AgentState) -> AgentState:  # type: ignore[override]
        result = self.crew_flow.run(state=state.model_dump())
        state.output = result.get("output")
        state.done = result.get("done", False)
        return state
