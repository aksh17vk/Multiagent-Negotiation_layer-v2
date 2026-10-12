from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"



def test_task_validation_success():
    response = client.post(
        "/api/v1/tasks/validate",
        json={
            "task_id": "task-001",
            "description": "Review authentication middleware",
            "repository_id": "repo-001",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "task_id": "task-001",
        "repository_id": "repo-001",
    }


def test_task_validation_rejects_short_description():
    response = client.post(
        "/api/v1/tasks/validate",
        json={
            "task_id": "task-002",
            "description": "fix",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["request_id"]
    assert "X-Request-ID" in response.headers
