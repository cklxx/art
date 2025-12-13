"""Task abstractions and routing."""
from typing import Dict
from pydantic import BaseModel

from .agent import Agent


class Task(BaseModel):
    id: str
    kind: str
    input: Dict
    config: Dict = {}


class TaskRouter:
    def __init__(self, registry: Dict[str, Agent]):
        self.registry = registry

    def route(self, task: Task) -> Agent:
        if task.kind not in self.registry:
            raise KeyError(f"No agent registered for task kind: {task.kind}")
        return self.registry[task.kind]
