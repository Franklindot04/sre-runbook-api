import pytest
from fastapi.testclient import TestClient

from sre_runbook_api.auth import create_access_token, hash_password
from sre_runbook_api.database import Base, SessionLocal, engine
from sre_runbook_api.main import app
from sre_runbook_api.models import User


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = User(
        email="fixture@example.com",
        display_name="Fixture User",
        password_hash=hash_password("fixture-password-123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(str(user.id))
    db.close()

    with TestClient(
        app,
        headers={
            "X-API-Key": "development-only-change-me",
            "Authorization": f"Bearer {access_token}",
        },
    ) as test_client:
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


def test_api_requires_authentication() -> None:
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.get("/api/v1/services")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_service_list_supports_pagination(client: TestClient) -> None:
    for name in ("Alpha API", "Bravo API", "Charlie API"):
        response = client.post(
            "/api/v1/services",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "description": "Test service.",
                "owner_team": "Platform",
            },
        )
        assert response.status_code == 201

    response = client.get("/api/v1/services?limit=2&offset=1")

    assert response.status_code == 200
    assert [service["name"] for service in response.json()] == [
        "Bravo API",
        "Charlie API",
    ]


def test_collection_pagination_rejects_invalid_values(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/services?limit=101")

    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


def test_service_search_filter_composes_with_pagination(
    client: TestClient,
) -> None:
    for name in ("Payments API", "Payments Worker", "Orders API"):
        response = client.post(
            "/api/v1/services",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "description": "Test service.",
                "owner_team": "Platform",
            },
        )
        assert response.status_code == 201

    response = client.get(
        "/api/v1/services?search=payments&limit=1&offset=1"
    )

    assert response.status_code == 200
    assert [service["name"] for service in response.json()] == [
        "Payments Worker"
    ]


def test_runbook_search_filters_title_and_slug(client: TestClient) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "Search Service",
            "slug": "search-service",
            "description": "Test service.",
            "owner_team": "Platform",
        },
    )
    service_id = service_response.json()["id"]

    for title, slug in (
        ("Database Recovery", "database-recovery"),
        ("Cache Recovery", "cache-recovery"),
    ):
        response = client.post(
            "/api/v1/runbooks",
            json={
                "service_id": service_id,
                "title": title,
                "slug": slug,
                "summary": "Recovery procedure.",
                "severity": "high",
                "content": "Follow the recovery procedure.",
            },
        )
        assert response.status_code == 201

    response = client.get("/api/v1/runbooks?search=database")

    assert response.status_code == 200
    assert [runbook["slug"] for runbook in response.json()] == [
        "database-recovery"
    ]


def test_service_list_returns_total_count_for_filtered_results(
    client: TestClient,
) -> None:
    for name in ("Payments API", "Payments Worker", "Orders API"):
        response = client.post(
            "/api/v1/services",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "description": "Test service.",
                "owner_team": "Platform",
            },
        )
        assert response.status_code == 201

    response = client.get(
        "/api/v1/services?search=payments&limit=1&offset=1"
    )

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "2"
    assert len(response.json()) == 1


def test_invalid_api_key_emits_safe_auth_failure_log(
    client: TestClient,
    caplog,
) -> None:
    import json
    import logging

    with caplog.at_level(logging.INFO, logger="sre_runbook_api.auth"):
        response = client.get(
            "/api/v1/services",
            headers={"X-API-Key": "invalid-key"},
        )

    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "sre_runbook_api.auth"
    ]

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key."
    assert len(records) == 1
    assert records[0]["event"] == "auth_failure"
    assert records[0]["reason"] == "invalid_api_key"
    assert records[0]["path"] == "/api/v1/services"
    assert "invalid-key" not in caplog.text


def test_missing_api_key_emits_safe_auth_failure_log(
    caplog,
) -> None:
    import json
    import logging

    with TestClient(app) as unauthenticated_client:
        with caplog.at_level(logging.INFO, logger="sre_runbook_api.auth"):
            response = unauthenticated_client.get("/api/v1/services")

    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "sre_runbook_api.auth"
    ]

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert len(records) == 1
    assert records[0]["event"] == "auth_failure"
    assert records[0]["reason"] == "missing_api_key"


def test_valid_api_key_emits_auth_success_log(
    client: TestClient,
    caplog,
) -> None:
    import json
    import logging

    with caplog.at_level(logging.INFO, logger="sre_runbook_api.auth"):
        response = client.get("/api/v1/services")

    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "sre_runbook_api.auth"
    ]

    assert response.status_code == 200
    assert len(records) == 1
    assert records[0]["event"] == "auth_success"
    assert records[0]["reason"] == "valid_api_key"
    assert "development-only-change-me" not in caplog.text

def test_register_user_does_not_expose_password_hash(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "display_name": "Alice",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["display_name"] == "Alice"
    assert body["is_active"] is True
    assert "password_hash" not in body


def test_register_user_normalizes_email_and_rejects_duplicates(
    client: TestClient,
) -> None:
    payload = {
        "email": " Alice@Example.com ",
        "password": "correct-horse-battery-staple",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    duplicate_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert first_response.json()["email"] == "alice@example.com"
    assert duplicate_response.status_code == 409


def test_login_returns_bearer_token(client: TestClient) -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "LOGIN@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    assert registration.status_code == 201
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-login@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-login@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_services_are_isolated_between_users(
    client: TestClient,
) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "Owned Service",
            "slug": "owned-service",
            "description": "Owned by the fixture user.",
            "owner_team": "Platform",
        },
    )

    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    original_headers = dict(client.headers)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other-user@example.com",
            "display_name": "Other User",
            "password": "other-password-123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "other-user@example.com",
            "password": "other-password-123",
        },
    )
    assert login_response.status_code == 200

    other_token = login_response.json()["access_token"]
    client.headers.update(
        {"Authorization": f"Bearer {other_token}"}
    )

    list_response = client.get("/api/v1/services")
    assert list_response.status_code == 200
    assert list_response.json() == []

    runbook_response = client.post(
        "/api/v1/runbooks",
        json={
            "service_id": service_id,
            "title": "Unauthorized Runbook",
            "slug": "unauthorized-runbook",
            "summary": "Should not be created.",
            "severity": "medium",
            "content": "Unauthorized content.",
        },
    )
    assert runbook_response.status_code == 404

    client.headers.clear()
    client.headers.update(original_headers)