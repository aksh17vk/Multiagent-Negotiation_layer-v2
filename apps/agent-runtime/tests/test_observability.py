import json
import logging

from app.observability.context import (
    get_task_id,
    get_trace_id,
    new_trace_id,
    reset_execution_context,
    set_execution_context,
)
from app.observability.events import (
    ExecutionEvent,
    ExecutionTimer,
    emit_event,
)


def test_trace_ids_are_unique():
    assert new_trace_id() != new_trace_id()


def test_execution_context_is_set_and_reset():
    tokens = set_execution_context("task-001", "trace-001")

    try:
        assert get_task_id() == "task-001"
        assert get_trace_id() == "trace-001"
    finally:
        reset_execution_context(tokens)

    assert get_task_id() is None
    assert get_trace_id() is None


def test_event_contains_execution_context_and_safe_metadata(caplog):
    tokens = set_execution_context("task-001", "trace-001")

    try:
        with caplog.at_level(logging.INFO, logger="mnl.execution"):
            emit_event(
                ExecutionEvent.AGENT_STARTED,
                metadata={
                    "agent_name": "backend",
                    "status": "started",
                    "secret": "must-not-appear",
                    "prompt": "private task content",
                },
            )

        event_records = [
            record for record in caplog.records
            if record.name == "mnl.execution"
        ]
        assert event_records

        message = event_records[-1].getMessage()
        payload = json.loads(
            message.removeprefix("execution_event ")
        )

        assert payload["event"] == "agent.started"
        assert payload["task_id"] == "task-001"
        assert payload["trace_id"] == "trace-001"
        assert payload["metadata"]["agent_name"] == "backend"
        assert "secret" not in message
        assert "private task content" not in message
    finally:
        reset_execution_context(tokens)


def test_execution_timer_measures_duration():
    with ExecutionTimer() as timer:
        sum(range(1000))

    assert timer.duration_ms >= 0