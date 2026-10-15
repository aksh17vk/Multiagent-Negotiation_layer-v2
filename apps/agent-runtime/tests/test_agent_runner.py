
import asyncio
import json
import logging

import pytest

from app.agents.base import BaseAgent
from app.agents.runner import run_agent
from app.schemas.agent import AgentResult, TaskRequest

from app.observability.context import (
    get_task_id,
    get_trace_id,
    set_execution_context,
    reset_execution_context,
)


class SuccessfulAgent(BaseAgent):
    agent_name = "backend"

    async def execute(self, task: TaskRequest) -> AgentResult:
        return AgentResult(
            agent_name="backend",
            status="completed",
            summary="Task completed successfully.",
            evidence=[],
        )


class BrokenAgent(BaseAgent):
    agent_name = "security"

    async def execute(self, task: TaskRequest) -> AgentResult:
        raise RuntimeError("Internal sensitive error")


def make_task() -> TaskRequest:
    return TaskRequest(
        task_id="task-001",
        description="Review the repository backend implementation.",
    )


def read_events(caplog):
    events = []

    for record in caplog.records:
        if record.name != "mnl.execution":
            continue

        message = record.getMessage()
        if message.startswith("execution_event "):
            payload = message.removeprefix("execution_event ")
            events.append(json.loads(payload))

    return events


def test_runner_emits_started_and_completed_events(caplog):
    caplog.set_level(logging.INFO, logger="mnl.execution")

    result = asyncio.run(run_agent(SuccessfulAgent(), make_task()))

    assert result.status == "completed"

    events = read_events(caplog)
    event_names = [event["event"] for event in events]

    assert event_names == ["agent.started", "agent.completed"]
    assert events[-1]["metadata"]["agent_name"] == "backend"
    assert isinstance(events[-1]["metadata"]["duration_ms"], (int, float))


def test_runner_logs_failure_and_reraises_exception(caplog):
    caplog.set_level(logging.INFO, logger="mnl.execution")

    with pytest.raises(RuntimeError, match="Internal sensitive error"):
        asyncio.run(run_agent(BrokenAgent(), make_task()))

    events = read_events(caplog)
    event_names = [event["event"] for event in events]

    assert event_names == ["agent.started", "agent.failed"]

    failure = events[-1]
    assert failure["metadata"]["error_code"] == "AGENT_EXECUTION_ERROR"
    assert "Internal sensitive error" not in failure["metadata"].values()

def test_runner_rejects_mismatched_agent_identity(caplog):
    import asyncio
    import logging

    import pytest

    caplog.set_level(logging.INFO, logger="mnl.execution")

    class MismatchedAgent(BaseAgent):
        agent_name = "backend"

        async def execute(self, task: TaskRequest) -> AgentResult:
            return AgentResult(
                agent_name="security",
                status="completed",
                summary="Mismatched identity.",
            )

    with pytest.raises(ValueError, match="identity"):
        asyncio.run(run_agent(MismatchedAgent(), make_task()))



def test_runner_emits_failed_event_when_agent_returns_failed_result(caplog):
    import asyncio
    import json
    import logging

    caplog.set_level(logging.INFO, logger="mnl.execution")

    class FailedResultAgent(BaseAgent):
        agent_name = "backend"

        async def execute(self, task: TaskRequest) -> AgentResult:
            return AgentResult(
                agent_name="backend",
                status="failed",
                summary="The task could not be completed.",
            )

    result = asyncio.run(
        run_agent(FailedResultAgent(), make_task())
    )

    assert result.status == "failed"

    events = []
    for record in caplog.records:
        if record.name != "mnl.execution":
            continue

        message = record.getMessage()
        if message.startswith("execution_event "):
            payload = message.removeprefix("execution_event ")
            events.append(json.loads(payload))

    event_names = [event["event"] for event in events]

    assert event_names == ["agent.started", "agent.failed"]
    assert events[-1]["metadata"]["agent_name"] == "backend"
    assert events[-1]["metadata"]["error_code"] == "AGENT_REPORTED_FAILURE"

   
def test_runner_preserves_existing_task_and_trace_context(caplog):
    caplog.set_level(logging.INFO, logger="mnl.execution")

    tokens = set_execution_context(
        task_id="task-context-001",
        trace_id="trace-context-001",
    )

    try:
        asyncio.run(
            run_agent(
                SuccessfulAgent(),
                TaskRequest(
                    task_id="task-context-001",
                    description="Review backend execution context.",
                ),
            )
        )
    finally:
        reset_execution_context(tokens)

    events = []

    for record in caplog.records:
        if record.name != "mnl.execution":
            continue

        message = record.getMessage()
        if message.startswith("execution_event "):
            payload = message.removeprefix("execution_event ")
            events.append(json.loads(payload))

    assert len(events) >= 2

    for event in events:
        assert event["task_id"] == "task-context-001"
        assert event["trace_id"] == "trace-context-001"



def test_runner_emits_execution_timing_and_metadata(caplog):
    import asyncio
    import json
    import logging

    caplog.set_level(logging.INFO, logger="mnl.execution")

    result = asyncio.run(
        run_agent(
            SuccessfulAgent(),
            TaskRequest(
                task_id="task-timing-001",
                description="Verify agent execution timing metadata.",
            ),
        )
    )

    assert result.status == "completed"

    events = []

    for record in caplog.records:
        if record.name != "mnl.execution":
            continue

        message = record.getMessage()

        if message.startswith("execution_event "):
            payload = message.removeprefix("execution_event ")
            events.append(json.loads(payload))

    started_events = [
        event for event in events
        if event["event"] == "agent.started"
    ]
    completed_events = [
        event for event in events
        if event["event"] == "agent.completed"
    ]

    assert len(started_events) == 1
    assert len(completed_events) == 1

    metadata = completed_events[0]["metadata"]

    assert metadata["agent_name"] == "backend"
    assert metadata["status"] == "completed"
    assert isinstance(metadata["duration_ms"], (int, float))
    assert metadata["duration_ms"] >= 0


def test_runner_emits_failure_event_when_agent_raises(caplog):
    import asyncio
    import json
    import logging

    caplog.set_level(logging.INFO, logger="mnl.execution")

    class CrashingAgent(BaseAgent):
        agent_name = "backend"

        async def execute(self, task: TaskRequest) -> AgentResult:
            raise RuntimeError("Simulated agent failure")

    with pytest.raises(RuntimeError, match="Simulated agent failure"):
        asyncio.run(
            run_agent(
                CrashingAgent(),
                TaskRequest(
                    task_id="task-crash-001",
                    description="Test unexpected agent execution failure.",
                ),
            )
        )

    events = []

    for record in caplog.records:
        if record.name != "mnl.execution":
            continue

        message = record.getMessage()

        if message.startswith("execution_event "):
            payload = message.removeprefix("execution_event ")
            events.append(json.loads(payload))

    event_names = [event["event"] for event in events]

    assert event_names == ["agent.started", "agent.failed"]
    assert events[-1]["metadata"]["error_code"] == "AGENT_EXECUTION_ERROR"
    assert events[-1]["metadata"]["status"] == "failed"

def test_runner_rejects_mismatched_agent_identity():
    import asyncio

    class MismatchedAgent(BaseAgent):
        agent_name = "backend"

        async def execute(self, task: TaskRequest) -> AgentResult:
            return AgentResult(
                agent_name="security",
                status="completed",
                summary="Intentional identity mismatch.",
            )

    with pytest.raises(
        ValueError,
        match="Agent result identity does not match",
    ):
        asyncio.run(
            run_agent(
                MismatchedAgent(),
                TaskRequest(
                    task_id="task-identity-001",
                    description="Verify agent result identity validation.",
                ),
            )
        )