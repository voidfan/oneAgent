"""Execution tracing - records agent decision and execution traces."""
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TraceSpan:
    """A single span in an execution trace."""
    id: str
    name: str
    trace_id: str
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    status: str = "running"  # running | completed | error

    @property
    def duration_ms(self) -> Optional[int]:
        if self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {},
        })

    def finish(self, status: str = "completed") -> None:
        self.end_time = time.monotonic()
        self.status = status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class TraceCollector:
    """Collects and manages execution traces."""

    def __init__(self):
        self._traces: dict[str, list[TraceSpan]] = {}
        self._active_spans: dict[str, TraceSpan] = {}

    def start_trace(self, name: str, attributes: Optional[dict] = None) -> str:
        """Start a new trace and return the trace ID."""
        trace_id = str(uuid.uuid4())
        span = TraceSpan(
            id=str(uuid.uuid4()),
            name=name,
            trace_id=trace_id,
            attributes=attributes or {},
        )
        self._traces[trace_id] = [span]
        self._active_spans[trace_id] = span
        logger.debug("trace_started", trace_id=trace_id, name=name)
        return trace_id

    def start_span(
        self,
        trace_id: str,
        name: str,
        parent_id: Optional[str] = None,
        attributes: Optional[dict] = None,
    ) -> str:
        """Start a new span within a trace."""
        span = TraceSpan(
            id=str(uuid.uuid4()),
            name=name,
            trace_id=trace_id,
            parent_id=parent_id or (
                self._active_spans[trace_id].id if trace_id in self._active_spans else None
            ),
            attributes=attributes or {},
        )
        if trace_id in self._traces:
            self._traces[trace_id].append(span)
        else:
            self._traces[trace_id] = [span]
        self._active_spans[f"{trace_id}:{span.id}"] = span
        return span.id

    def add_event(self, trace_id: str, span_id: str, name: str, attributes: Optional[dict] = None) -> None:
        """Add an event to a span."""
        key = f"{trace_id}:{span_id}"
        span = self._active_spans.get(key)
        if span:
            span.add_event(name, attributes)

    def end_span(self, trace_id: str, span_id: str, status: str = "completed") -> None:
        """End a span."""
        key = f"{trace_id}:{span_id}"
        span = self._active_spans.pop(key, None)
        if span:
            span.finish(status)

    def end_trace(self, trace_id: str, status: str = "completed") -> None:
        """End a trace."""
        span = self._active_spans.pop(trace_id, None)
        if span:
            span.finish(status)
        logger.debug("trace_ended", trace_id=trace_id, status=status)

    def get_trace(self, trace_id: str) -> list[dict]:
        """Get all spans for a trace."""
        spans = self._traces.get(trace_id, [])
        return [s.to_dict() for s in spans]

    def get_recent_traces(self, limit: int = 50) -> list[dict]:
        """Get recent traces summary."""
        traces = []
        for trace_id, spans in list(self._traces.items())[-limit:]:
            root = spans[0] if spans else None
            traces.append({
                "trace_id": trace_id,
                "name": root.name if root else "unknown",
                "span_count": len(spans),
                "status": root.status if root else "unknown",
                "duration_ms": root.duration_ms if root else None,
            })
        return traces

    def clear(self) -> None:
        """Clear all traces."""
        self._traces.clear()
        self._active_spans.clear()
