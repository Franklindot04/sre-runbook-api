from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from sre_runbook_api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from sre_runbook_api.config import get_settings

ALGORITHM = "HS256"


def test_password_hash_is_not_plaintext() -> None:
    password = "correct-horse-battery-staple"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_access_token_round_trip() -> None:
    token = create_access_token("user-123")

    assert decode_access_token(token) == "user-123"


def test_invalid_access_token_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-valid-token")

    assert exc_info.value.status_code == 401


def test_access_token_signed_with_wrong_secret_is_rejected() -> None:
    token = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "untrusted-test-secret-with-enough-length",
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired access token."


def test_expired_access_token_is_rejected() -> None:
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired access token."


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        ({}, "Invalid access token."),
        ({"sub": ""}, "Invalid access token."),
        ({"sub": 123}, "Invalid or expired access token."),
    ],
)
def test_access_token_with_missing_or_invalid_subject_is_rejected(
    payload: dict[str, object],
    expected_detail: str,
) -> None:
    settings = get_settings()
    payload = {
        **payload,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == expected_detail
