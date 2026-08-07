import pytest
from fastapi.testclient import TestClient

from sre_runbook_api.database import Base, engine
from sre_runbook_api.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def test_create_and_list_service(client: TestClient) -> None:
    response = client.post(
        "/api/v1/services",
        json={
            "name": "Payments API",
            "slug": "payments-api",
            "description": "Payment processing service.",
            "owner_team": "Payments Platform",
        },
    )

    assert response.status_code == 201
    service = response.json()
    assert service["name"] == "Payments API"

    response = client.get("/api/v1/services")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_and_get_runbook(client: TestClient) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "Orders API",
            "slug": "orders-api",
            "description": "Order management service.",
            "owner_team": "Commerce Platform",
        },
    )

    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    response = client.post(
        "/api/v1/runbooks",
        json={
            "service_id": service_id,
            "title": "Orders API degradation",
            "slug": "orders-api-degradation",
            "summary": "Steps for investigating elevated latency.",
            "severity": "high",
            "content": (
                "Check service health, inspect recent deployments, "
                "review dependency latency, and communicate status."
            ),
        },
    )

    assert response.status_code == 201
    runbook_id = response.json()["id"]

    response = client.get(f"/api/v1/runbooks/{runbook_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Orders API degradation"


def test_runbook_requires_existing_service(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runbooks",
        json={
            "service_id": 999999,
            "title": "Missing service runbook",
            "slug": "missing-service-runbook",
            "summary": "This should fail because the service does not exist.",
            "severity": "medium",
            "content": "This runbook should not be created.",
        },
    )

    assert response.status_code == 404

def test_create_alert_and_incident(client: TestClient) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "Checkout API",
            "slug": "checkout-api",
            "description": "Customer checkout service.",
            "owner_team": "Commerce Platform",
        },
    )

    service_id = service_response.json()["id"]

    alert_response = client.post(
        "/api/v1/alerts",
        json={
            "service_id": service_id,
            "fingerprint": "checkout-latency-prod",
            "name": "Checkout latency elevated",
            "severity": "high",
            "source": "prometheus",
            "description": "Checkout latency exceeded the production threshold.",
        },
    )

    assert alert_response.status_code == 201
    alert_id = alert_response.json()["id"]

    incident_response = client.post(
        "/api/v1/incidents",
        json={
            "service_id": service_id,
            "alert_id": alert_id,
            "title": "Checkout latency incident",
            "summary": "Customers are experiencing slow checkout requests.",
            "severity": "high",
        },
    )

    assert incident_response.status_code == 201
    incident = incident_response.json()
    assert incident["status"] == "open"
    assert incident["alert_id"] == alert_id
