import pytest
from pydantic import SecretStr, ValidationError

from sre_runbook_api.config import DEVELOPMENT_API_KEY, Settings


def test_development_allows_local_api_key() -> None:
    settings = Settings(
        environment="development",
        api_key=SecretStr(DEVELOPMENT_API_KEY),
    )

    assert settings.api_key.get_secret_value() == DEVELOPMENT_API_KEY


def test_production_rejects_development_api_key() -> None:
    with pytest.raises(ValidationError, match="explicitly configured"):
        Settings(
            environment="production",
            api_key=SecretStr(DEVELOPMENT_API_KEY),
        )


def test_staging_requires_a_long_api_key() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            environment="staging",
            api_key=SecretStr("too-short"),
        )


def test_production_accepts_a_long_api_key() -> None:
    settings = Settings(
        environment="production",
        api_key=SecretStr("p" * 32),
    )

    assert settings.environment == "production"
