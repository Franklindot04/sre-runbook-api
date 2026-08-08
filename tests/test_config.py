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
        jwt_secret_key=SecretStr("j" * 32),
    )

    assert settings.environment == "production"


def test_log_level_defaults_to_info(monkeypatch) -> None:
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings()

    assert settings.log_level == "INFO"


def test_log_level_is_case_insensitive() -> None:
    settings = Settings(log_level="debug")

    assert settings.log_level == "DEBUG"


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings(log_level="verbose")


def test_production_rejects_development_jwt_secret(monkeypatch) -> None:
    from pydantic import ValidationError

    from sre_runbook_api.config import Settings

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "a" * 32)
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "development-only-jwt-secret-change-me",
    )

    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings()


def test_production_accepts_explicit_jwt_secret(monkeypatch) -> None:
    from sre_runbook_api.config import Settings

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "a" * 32)
    monkeypatch.setenv("JWT_SECRET_KEY", "b" * 32)

    settings = Settings()

    assert settings.environment == "production"
