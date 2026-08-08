from fastapi.testclient import TestClient

from sre_runbook_api.main import app

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_response_contains_generated_correlation_id() -> None:
    response = client.get("/health/live")

    correlation_id = response.headers.get("X-Correlation-ID")

    assert response.status_code == 200
    assert correlation_id is not None
    assert len(correlation_id) == 36


def test_request_correlation_id_is_preserved() -> None:
    correlation_id = "12345678-1234-4234-8234-123456789abc"

    response = client.get(
        "/health/live",
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_invalid_correlation_id_is_replaced() -> None:
    response = client.get(
        "/health/live",
        headers={"X-Correlation-ID": "not-a-valid-id"},
    )

    returned_id = response.headers["X-Correlation-ID"]

    assert response.status_code == 200
    assert returned_id != "not-a-valid-id"
    assert len(returned_id) == 36


def test_http_errors_include_error_contract() -> None:
    response = client.get("/does-not-exist")

    body = response.json()

    assert response.status_code == 404
    assert body["detail"] == "Not Found"
    assert body["error_code"] == "http_error"
    assert body["correlation_id"] == response.headers["X-Correlation-ID"]


def test_validation_errors_include_error_contract() -> None:
    response = client.post(
        "/api/v1/services",
        json={"name": "Invalid"},
        headers={
            "X-API-Key": "development-only-change-me",
            "X-Correlation-ID": "12345678-1234-4234-8234-123456789abc",
        },
    )

    body = response.json()

    assert response.status_code == 422
    assert body["error_code"] == "validation_error"
    assert body["correlation_id"] == "12345678-1234-4234-8234-123456789abc"
