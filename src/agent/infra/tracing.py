"""Tracing hooks placeholder with in-memory recorder."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

from pydantic import BaseModel


@dataclass
class TraceEvent:
    name: str
    start_ns: int
    end_ns: int
    attributes: Dict[str, str]

    @property
    def duration_ms(self) -> float:
        return (self.end_ns - self.start_ns) / 1_000_000


class InMemoryTracer:
    def __init__(self) -> None:
        self.events: List[TraceEvent] = []

    @contextmanager
    def span(self, name: str, **attributes: str) -> Iterator[None]:
        start = time.time_ns()
        try:
            yield
        finally:
            end = time.time_ns()
            self.events.append(TraceEvent(name=name, start_ns=start, end_ns=end, attributes=attributes))

    def latest(self, name: Optional[str] = None) -> Optional[TraceEvent]:
        for event in reversed(self.events):
            if name is None or event.name == name:
                return event
        return None

    def export(self, limit: int | None = None) -> List["TraceEventPayload"]:
        """Return recent events as serializable payloads."""

        tail = self.events[-limit:] if limit else self.events
        return [TraceEventPayload.from_event(event) for event in tail]

    def timeline(self, task_id: Optional[str] = None, limit: int | None = None) -> List["TraceTimeline"]:
        """Return grouped spans ordered by start time for replay timelines."""

        filtered = self.events[-limit:] if limit else self.events
        buckets: Dict[str, List[TraceEvent]] = {}
        for event in filtered:
            tid = event.attributes.get("task_id", "unknown")
            if task_id and tid != task_id:
                continue
            buckets.setdefault(tid, []).append(event)

        timelines: List[TraceTimeline] = []
        for tid, events in buckets.items():
            events_sorted = sorted(events, key=lambda e: e.start_ns)
            start_ref = events_sorted[0].start_ns
            steps = [TraceStep.from_event(event, start_ref=start_ref) for event in events_sorted]
            total_ms = steps[-1].end_ms if steps else 0.0
            timelines.append(TraceTimeline(task_id=tid, total_ms=total_ms, events=steps))
        return timelines


_default_tracer = InMemoryTracer()


@contextmanager
def traced_span(name: str, **attributes: str) -> Iterator[None]:
    """Simple context manager to instrument critical sections without external deps."""

    with _default_tracer.span(name, **attributes):
        yield


def get_tracer() -> InMemoryTracer:
    return _default_tracer


class TraceEventPayload(BaseModel):
    name: str
    duration_ms: float
    attributes: Dict[str, str]

    @classmethod
    def from_event(cls, event: TraceEvent) -> "TraceEventPayload":
        return cls(
            name=event.name,
            duration_ms=event.duration_ms,
            attributes=event.attributes,
        )


class TraceStep(BaseModel):
    name: str
    start_ms: float
    end_ms: float
    duration_ms: float
    attributes: Dict[str, str]

    @classmethod
    def from_event(cls, event: TraceEvent, start_ref: int) -> "TraceStep":
        start_ms = (event.start_ns - start_ref) / 1_000_000
        end_ms = (event.end_ns - start_ref) / 1_000_000
        return cls(
            name=event.name,
            start_ms=start_ms,
            end_ms=end_ms,
            duration_ms=end_ms - start_ms,
            attributes=event.attributes,
        )


class TraceTimeline(BaseModel):
    task_id: str
    total_ms: float
    events: List[TraceStep]
