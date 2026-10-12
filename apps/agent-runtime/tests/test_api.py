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


def test_request_ids_are_unique():
    first = client.get("/health")
    second = client.get("/health")

    assert first.status_code == 200
    assert second.status_code == 200

    first_id = first.headers["X-Request-ID"]
    second_id = second.headers["X-Request-ID"]

    assert first_id
    assert second_id
    assert first_id != second_id


def test_validation_error_has_consistent_format():
    response = client.post(
        "/api/v1/tasks/validate",
        json={
            "task_id": "task-invalid",
            "description": "fix",
        },
    )

    assert response.status_code == 422
    assert "X-Request-ID" in response.headers

    body = response.json()

    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == (
        "The request data is invalid."
    )
    assert (
        body["error"]["request_id"]
        == response.headers["X-Request-ID"]
    )


def test_successful_task_response_matches_contract():
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
