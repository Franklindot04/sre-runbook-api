import pytest
from fastapi import HTTPException

from sre_runbook_api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


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
