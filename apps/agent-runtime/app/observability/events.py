import json
import logging
from enum import StrEnum
from time import perf_counter
from typing import Any

from app.observability.context import get_task_id, get_trace_id

logger = logging.getLogger("mnl.execution")


class ExecutionEvent(StrEnum):
    TASK_RECEIVED = "task.received"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    CONTEXT_OVERFLOW = "context.overflow"
    TASK_VALIDATION_COMPLETED = "task.validation.completed"
    TASK_VALIDATION_FAILED = "task.validation.failed"


_ALLOWED_METADATA = {
    "agent_name",
    "status",
    "duration_ms",
    "error_code",
    "context_tokens",
    "token_budget",
    "overflow_tokens",
}


def emit_event(
    event: ExecutionEvent,
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a structured execution event without raw task content."""
    safe_metadata = {
        key: value
        for key, value in (metadata or {}).items()
        if key in _ALLOWED_METADATA
        and isinstance(value, (str, int, float, bool, type(None)))
    }

    payload = {
        "event": event.value,
        "task_id": get_task_id(),
        "trace_id": get_trace_id(),
        "metadata": safe_metadata,
    }

    logger.info(
        "execution_event %s",
        json.dumps(payload, sort_keys=True),
    )


class ExecutionTimer:
    """Measure elapsed wall-clock time for an operation."""

    def __enter__(self):
        self._started_at = perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.duration_ms = round(
            (perf_counter() - self._started_at) * 1000,
            2,
        )
        return False