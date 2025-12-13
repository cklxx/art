"""Composable reasoning graphs for summarization and decision support."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from .state import AgentState
from .io import KnowledgeBundle, KnowledgeSlice

Step = Callable[[AgentState], AgentState]


def summarization_graph() -> Iterable[Step]:
    """Basic summarization flow: collect highlights then synthesize output."""

    def collect_highlights(state: AgentState) -> AgentState:
        observation = state.observation or {}
        key_points = observation.get("key_points") or observation.get("bullets") or []
        state.working_memory.setdefault("highlights", []).extend(key_points)
        return state

    def synthesize(state: AgentState) -> AgentState:
        highlights = state.working_memory.get("highlights", [])
        summary = "; ".join(highlights) if highlights else str(state.observation)
        state.output = summary
        state.done = True
        return state

    return [collect_highlights, synthesize]


def decision_support_graph() -> Iterable[Step]:
    """Flow that weighs options and writes rationale into the state."""

    def evaluate_options(state: AgentState) -> AgentState:
        options: List[Dict[str, str]] = state.observation.get("options", [])
        chosen = options[0] if options else {"id": "n/a", "reason": "no options"}
        state.working_memory["choice"] = chosen
        return state

    def document_rationale(state: AgentState) -> AgentState:
        choice = state.working_memory.get("choice", {})
        rationale = choice.get("reason") or "auto-selected first option"
        state.output = f"choice={choice.get('id')} rationale={rationale}"
        state.done = True
        return state

    return [evaluate_options, document_rationale]


def multimodal_mixer_graph() -> Iterable[Step]:
    """Mix text, image, and audio cues step-by-step to keep modality context."""

    def collect_signals(state: AgentState) -> AgentState:
        observation = state.observation or {}
        texts = observation.get("texts", [])
        images = observation.get("images", [])
        audio = observation.get("audio", [])

        cues = []
        for doc in texts:
            content = doc.get("content") or ""
            if content:
                cues.append(f"text:{content}")
        for img in images:
            caption = img.get("caption") or img.get("alt") or ""
            if caption:
                cues.append(f"image:{caption}")
        for clip in audio:
            transcript = clip.get("transcript") or ""
            if transcript:
                cues.append(f"audio:{transcript}")

        state.working_memory["modal_cues"] = cues
        return state

    def synthesize_rationale(state: AgentState) -> AgentState:
        cues = state.working_memory.get("modal_cues", [])
        state.working_memory["highlights"] = cues or ["no multimodal cues provided"]
        state.output = " | ".join(cues[:3]) if cues else "No signals found"
        state.done = True
        state.observation.setdefault("modality", "mixed")
        state.observation.setdefault("sources", [])
        state.observation.setdefault("tags", ["multimodal" if cues else "empty"])
        return state

    return [collect_signals, synthesize_rationale]


def produce_knowledge_bundle(state: AgentState) -> KnowledgeBundle:
    """Convert an agent state into a normalized knowledge bundle."""

    highlights = state.working_memory.get("highlights") or []
    modality = state.observation.get("modality", "mixed")
    slice = KnowledgeSlice(
        id=state.task_id,
        summary=state.output or "",
        highlights=[str(h) for h in highlights] or [state.output or ""],
        modality=modality,
        source_refs=list(state.observation.get("sources", [])),
        tags=list(state.observation.get("tags", [])),
    )
    return KnowledgeBundle(slices=[slice])
