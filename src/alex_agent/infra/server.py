"""FastAPI server exposing the agent loop and paper review helpers."""
from fastapi import FastAPI

from ..core.loop import run_loop
from ..core.state import AgentState
from ..core.agent import BaseLLMAgent
from ..llm.judge_models import EchoJudge
from ..apps.paper_review import (
    ImageBatchRequest,
    ImageBatchResponse,
    PaperAnalysisRequest,
    PaperAnalysisResponse,
    analyze_paper,
    generate_review_images,
)

app = FastAPI(title="alex-agent API", version="0.1.0")


def create_agent() -> BaseLLMAgent:
    llm = EchoJudge()
    return BaseLLMAgent(name="echo", llm=llm)


def create_app() -> FastAPI:
    return app


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tasks/{task_id}")
def run_task(task_id: str, payload: dict) -> dict:
    agent = create_agent()
    state = AgentState(task_id=task_id, observation=payload)
    final_state = run_loop(agent, state, max_steps=1)
    return final_state.model_dump()


@app.post("/review/analyze", response_model=PaperAnalysisResponse)
def review_analyze(payload: PaperAnalysisRequest) -> PaperAnalysisResponse:
    """Analyze a paper and produce candidate image prompts."""
    return analyze_paper(payload)


@app.post("/review/images", response_model=ImageBatchResponse)
def review_images(payload: ImageBatchRequest) -> ImageBatchResponse:
    """Generate (or regenerate) review images for the supplied prompts."""
    return generate_review_images(payload)
