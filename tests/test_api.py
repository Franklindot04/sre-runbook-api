from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from sre_runbook_api.auth import create_access_token, hash_password
from sre_runbook_api.config import get_settings
from sre_runbook_api.database import Base, SessionLocal, engine
from sre_runbook_api.main import app
from sre_runbook_api.models import User

API_KEY = "development-only-change-me"
ALGORITHM = "HS256"


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
            "X-API-Key": API_KEY,
            "Authorization": f"Bearer {access_token}",
        },
    ) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def _register_and_login(
    client: TestClient,
    *,
    email: str,
) -> str:
    password = "test-password-123"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Collection Test User",
            "password": password,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def _create_owned_operational_set(
    client: TestClient,
    *,
    prefix: str,
    service_name: str,
    service_slug: str,
    runbook_title: str,
    runbook_slug: str,
    alert_severity: str,
    incident_status: str = "open",
) -> dict[str, dict[str, object]]:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": service_name,
            "slug": service_slug,
            "description": f"{prefix} collection isolation service.",
            "owner_team": f"{prefix} Platform",
        },
    )
    assert service_response.status_code == 201
    service = service_response.json()

    runbook_response = client.post(
        "/api/v1/runbooks",
        json={
            "service_id": service["id"],
            "title": runbook_title,
            "slug": runbook_slug,
            "summary": f"{prefix} runbook for collection isolation.",
            "severity": "high",
            "content": (
                f"{prefix} operational procedure for ownership filtering "
                "coverage."
            ),
        },
    )
    assert runbook_response.status_code == 201
    runbook = runbook_response.json()

    alert_response = client.post(
        "/api/v1/alerts",
        json={
            "service_id": service["id"],
            "fingerprint": f"{service_slug}-collection-alert",
            "name": f"{prefix} Collection Alert",
            "severity": alert_severity,
            "source": "test-suite",
            "description": f"{prefix} alert for collection filtering tests.",
        },
    )
    assert alert_response.status_code == 201
    alert = alert_response.json()

    incident_response = client.post(
        "/api/v1/incidents",
        json={
            "service_id": service["id"],
            "alert_id": alert["id"],
            "title": f"{prefix} Collection Incident",
            "summary": f"{prefix} incident for collection filtering tests.",
            "severity": "high",
        },
    )
    assert incident_response.status_code == 201
    incident = incident_response.json()
    assert incident["status"] == incident_status

    return {
        "service": service,
        "runbook": runbook,
        "alert": alert,
        "incident": incident,
    }


def _assert_collection_contains_only(
    response,
    *,
    expected_id: int | None,
    hidden_values: set[str],
    total_count: str,
) -> None:
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == total_count

    items = response.json()
    if expected_id is None:
        assert items == []
    else:
        assert {item["id"] for item in items} == {expected_id}

    body_text = response.text
    for value in hidden_values:
        assert value not in body_text


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


def test_protected_route_accepts_valid_api_key_and_bearer_token(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/services")

    assert response.status_code == 200


def test_protected_route_rejects_missing_api_key(
    client: TestClient,
) -> None:
    bearer_token = client.headers["authorization"]

    with TestClient(app, headers={"Authorization": bearer_token}) as test_client:
        response = test_client.get("/api/v1/services")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_route_rejects_missing_bearer_token() -> None:
    with TestClient(app, headers={"X-API-Key": API_KEY}) as test_client:
        response = test_client.get("/api/v1/services")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    ("access_token", "expected_detail"),
    [
        ("not-a-valid-token", "Invalid or expired access token."),
        (
            jwt.encode(
                {
                    "sub": "123",
                    "exp": datetime.now(UTC) + timedelta(minutes=5),
                },
                "untrusted-test-secret-with-enough-length",
                algorithm=ALGORITHM,
            ),
            "Invalid or expired access token.",
        ),
        (
            jwt.encode(
                {
                    "sub": "123",
                    "exp": datetime.now(UTC) - timedelta(minutes=1),
                },
                get_settings().jwt_secret_key.get_secret_value(),
                algorithm=ALGORITHM,
            ),
            "Invalid or expired access token.",
        ),
        (
            jwt.encode(
                {
                    "exp": datetime.now(UTC) + timedelta(minutes=5),
                },
                get_settings().jwt_secret_key.get_secret_value(),
                algorithm=ALGORITHM,
            ),
            "Invalid access token.",
        ),
        (
            create_access_token("not-an-integer"),
            "Invalid access token.",
        ),
    ],
)
def test_protected_route_rejects_invalid_bearer_tokens_safely(
    access_token: str,
    expected_detail: str,
) -> None:
    with TestClient(
        app,
        headers={
            "X-API-Key": API_KEY,
            "Authorization": f"Bearer {access_token}",
        },
    ) as test_client:
        response = test_client.get("/api/v1/services")

    body = response.json()
    body_text = response.text

    assert response.status_code == 401
    assert body["detail"] == expected_detail
    assert body["error_code"] == "http_error"
    assert access_token not in body_text
    assert API_KEY not in body_text
    assert "password_hash" not in body_text
    assert "Traceback" not in body_text


def test_protected_route_rejects_token_for_missing_user_safely() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    access_token = create_access_token("999999")

    try:
        with TestClient(
            app,
            headers={
                "X-API-Key": API_KEY,
                "Authorization": f"Bearer {access_token}",
            },
        ) as test_client:
            response = test_client.get("/api/v1/services")
    finally:
        Base.metadata.drop_all(bind=engine)

    body_text = response.text

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert access_token not in body_text
    assert "999999" not in body_text
    assert "password_hash" not in body_text


def test_protected_route_rejects_token_for_inactive_user_safely() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inactive_user = User(
        email="inactive@example.com",
        display_name="Inactive User",
        password_hash=hash_password("inactive-password-123"),
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()
    db.refresh(inactive_user)
    access_token = create_access_token(str(inactive_user.id))
    db.close()

    try:
        with TestClient(
            app,
            headers={
                "X-API-Key": API_KEY,
                "Authorization": f"Bearer {access_token}",
            },
        ) as test_client:
            response = test_client.get("/api/v1/services")
    finally:
        Base.metadata.drop_all(bind=engine)

    body_text = response.text

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert access_token not in body_text
    assert "inactive@example.com" not in body_text
    assert "Inactive User" not in body_text
    assert "password_hash" not in body_text


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
    assert API_KEY not in caplog.text


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


def test_collection_filters_hide_other_users_resources(
    client: TestClient,
) -> None:
    first_user_resources = _create_owned_operational_set(
        client,
        prefix="First User",
        service_name="First User Confidential API",
        service_slug="first-user-confidential-api",
        runbook_title="First User Confidential Runbook",
        runbook_slug="first-user-confidential-runbook",
        alert_severity="critical",
    )

    second_token = _register_and_login(
        client,
        email="collection-second-user@example.com",
    )
    client.headers.update({"Authorization": f"Bearer {second_token}"})

    second_user_resources = _create_owned_operational_set(
        client,
        prefix="Second User",
        service_name="Second User Visible API",
        service_slug="second-user-visible-api",
        runbook_title="Second User Visible Runbook",
        runbook_slug="second-user-visible-runbook",
        alert_severity="critical",
    )

    first_service = first_user_resources["service"]
    first_runbook = first_user_resources["runbook"]
    first_alert = first_user_resources["alert"]
    first_incident = first_user_resources["incident"]
    second_service = second_user_resources["service"]
    second_runbook = second_user_resources["runbook"]
    second_alert = second_user_resources["alert"]
    second_incident = second_user_resources["incident"]

    hidden_service_values = {
        first_service["name"],
        first_service["slug"],
        first_service["description"],
    }
    hidden_runbook_values = {
        first_runbook["title"],
        first_runbook["slug"],
        first_runbook["summary"],
    }
    hidden_alert_values = {
        first_alert["name"],
        first_alert["fingerprint"],
        first_alert["description"],
    }
    hidden_incident_values = {
        first_incident["title"],
        first_incident["summary"],
    }

    _assert_collection_contains_only(
        client.get("/api/v1/services"),
        expected_id=second_service["id"],
        hidden_values=hidden_service_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/services?search=first-user-confidential"),
        expected_id=None,
        hidden_values=hidden_service_values,
        total_count="0",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/services?search=second-user-visible"),
        expected_id=second_service["id"],
        hidden_values=hidden_service_values,
        total_count="1",
    )

    _assert_collection_contains_only(
        client.get("/api/v1/runbooks"),
        expected_id=second_runbook["id"],
        hidden_values=hidden_runbook_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/runbooks?search=first-user-confidential"),
        expected_id=None,
        hidden_values=hidden_runbook_values,
        total_count="0",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/runbooks?search=second-user-visible"),
        expected_id=second_runbook["id"],
        hidden_values=hidden_runbook_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/runbooks?service_id={first_service['id']}"),
        expected_id=None,
        hidden_values=hidden_runbook_values,
        total_count="0",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/runbooks?service_id={second_service['id']}"),
        expected_id=second_runbook["id"],
        hidden_values=hidden_runbook_values,
        total_count="1",
    )

    _assert_collection_contains_only(
        client.get("/api/v1/alerts"),
        expected_id=second_alert["id"],
        hidden_values=hidden_alert_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/alerts?service_id={first_service['id']}"),
        expected_id=None,
        hidden_values=hidden_alert_values,
        total_count="0",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/alerts?service_id={second_service['id']}"),
        expected_id=second_alert["id"],
        hidden_values=hidden_alert_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/alerts?severity=critical"),
        expected_id=second_alert["id"],
        hidden_values=hidden_alert_values,
        total_count="1",
    )

    _assert_collection_contains_only(
        client.get("/api/v1/incidents"),
        expected_id=second_incident["id"],
        hidden_values=hidden_incident_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/incidents?service_id={first_service['id']}"),
        expected_id=None,
        hidden_values=hidden_incident_values,
        total_count="0",
    )
    _assert_collection_contains_only(
        client.get(f"/api/v1/incidents?service_id={second_service['id']}"),
        expected_id=second_incident["id"],
        hidden_values=hidden_incident_values,
        total_count="1",
    )
    _assert_collection_contains_only(
        client.get("/api/v1/incidents?status=open"),
        expected_id=second_incident["id"],
        hidden_values=hidden_incident_values,
        total_count="1",
    )


def test_runbook_detail_is_hidden_from_other_users(
    client: TestClient,
) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "Private Service",
            "slug": "private-service",
            "description": "Owned by the fixture user.",
            "owner_team": "Platform",
        },
    )
    assert service_response.status_code == 201

    runbook_response = client.post(
        "/api/v1/runbooks",
        json={
            "service_id": service_response.json()["id"],
            "title": "Private Runbook",
            "slug": "private-runbook",
            "summary": "Only the owning user should retrieve this runbook.",
            "severity": "medium",
            "content": "These operational steps belong to the owning user only.",
        },
    )
    assert runbook_response.status_code == 201
    runbook_id = runbook_response.json()["id"]

    original_headers = dict(client.headers)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "runbook-outsider@example.com",
            "display_name": "Runbook Outsider",
            "password": "outsider-password-123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "runbook-outsider@example.com",
            "password": "outsider-password-123",
        },
    )
    assert login_response.status_code == 200

    client.headers.update(
        {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    )

    response = client.get(f"/api/v1/runbooks/{runbook_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Runbook not found."

    client.headers.clear()
    client.headers.update(original_headers)
