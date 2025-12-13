"""Core state models for the Agent OS."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentMessage(BaseModel):
    role: str  # "user" / "assistant" / "tool" / "system"
    content: str
    meta: Dict[str, Any] = {}


class AgentState(BaseModel):
    task_id: str
    step: int = 0

    observation: Dict[str, Any] = {}
    working_memory: Dict[str, Any] = {}
    session_memory: Dict[str, Any] = {}
    long_term_refs: List[str] = []

    plan: List[str] = []
    actions: List[Dict[str, Any]] = []
    messages: List[AgentMessage] = []

    output: Optional[str] = None
    done: bool = False

    reward: Optional[float] = None
    scores: Dict[str, float] = {}
