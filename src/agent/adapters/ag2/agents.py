"""AG2 adapter turning a groupchat into an Agent."""
from ...core.agent import BaseLLMAgent
from ...core.state import AgentState


class AG2GroupAgent(BaseLLMAgent):
    def __init__(self, ag2_graph, name: str = "ag2-group"):
        super().__init__(name=name, llm=ag2_graph)
        self.ag2_graph = ag2_graph

    def step(self, state: AgentState) -> AgentState:  # type: ignore[override]
        result = self.ag2_graph.run(state=state.model_dump())
        state.output = result.get("output")
        state.done = result.get("done", False)
        return state
