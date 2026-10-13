import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_task_validation_emits_tracing_events(caplog):
    with caplog.at_level(logging.INFO, logger="mnl.execution"):
        response = client.post(
            "/api/v1/tasks/validate",
            json={
                "task_id": "trace-test-001",
                "description": "Review authentication middleware",
                "repository_id": "repo-test-001",
            },
        )

    assert response.status_code == 200

    records = [
        record
        for record in caplog.records
        if record.name == "mnl.execution"
        and "execution_event " in record.getMessage()
    ]

    events = [
        json.loads(
            record.getMessage().removeprefix("execution_event ")
        )
        for record in records
    ]

    received = next(
        event for event in events
        if event["event"] == "task.received"
    )
    
    completed = next(
        event for event in events
        if event["event"] == "task.validation.completed"
    )


    assert received["task_id"] == "trace-test-001"
    assert received["trace_id"]
    assert completed["trace_id"] == received["trace_id"]
    assert completed["metadata"]["status"] == "completed"
    assert completed["metadata"]["duration_ms"] >= 0


def test_separate_requests_get_separate_trace_ids(caplog):
    trace_ids = []

    with caplog.at_level(logging.INFO, logger="mnl.execution"):
        for task_id in ("trace-test-002", "trace-test-003"):
            response = client.post(
                "/api/v1/tasks/validate",
                json={
                    "task_id": task_id,
                    "description": "Inspect API request validation",
                    "repository_id": "repo-test-001",
                },
            )
            assert response.status_code == 200

    for record in caplog.records:
        if (
            record.name == "mnl.execution"
            and "execution_event " in record.getMessage()
        ):
            event = json.loads(
                record.getMessage().removeprefix("execution_event ")
            )
            if event["event"] == "task.received":
                trace_ids.append(event["trace_id"])

    assert len(trace_ids) >= 2
    assert trace_ids[-2] != trace_ids[-1]