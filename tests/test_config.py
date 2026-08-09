import pytest
from pydantic import SecretStr, ValidationError

from sre_runbook_api.config import (
    DEVELOPMENT_API_KEY,
    DEVELOPMENT_JWT_SECRET_KEY,
    Settings,
    get_settings,
)

SAFE_API_KEY = "synthetic-test-api-key-value-00001"
SAFE_JWT_SECRET = "synthetic-test-jwt-secret-value-001"
API_KEY_PLACEHOLDER = "replace-with-a-long-random-secret"
UNRELATED_SECRET = "synthetic-unrelated-secret-value"


@pytest.fixture(autouse=True)
def isolate_settings_environment(monkeypatch):
    get_settings.cache_clear()
    for name in (
        "APP_NAME",
        "APP_VERSION",
        "ENVIRONMENT",
        "DEBUG",
        "LOG_LEVEL",
        "DATABASE_URL",
        "API_KEY",
        "API_KEY_HEADER",
        "JWT_SECRET_KEY",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "UNRELATED_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    yield

    get_settings.cache_clear()


def build_settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


def test_development_allows_local_api_key() -> None:
    settings = build_settings(
        environment="development",
        api_key=SecretStr(DEVELOPMENT_API_KEY),
    )

    assert settings.api_key.get_secret_value() == DEVELOPMENT_API_KEY
    assert settings.jwt_secret_key.get_secret_value() == DEVELOPMENT_JWT_SECRET_KEY


def test_test_environment_allows_deterministic_defaults() -> None:
    settings = build_settings(environment="test")

    assert settings.environment == "test"
    assert settings.api_key.get_secret_value() == DEVELOPMENT_API_KEY
    assert settings.jwt_secret_key.get_secret_value() == DEVELOPMENT_JWT_SECRET_KEY


def test_explicit_safe_test_values_are_accepted() -> None:
    settings = build_settings(
        environment="test",
        api_key=SecretStr(SAFE_API_KEY),
        jwt_secret_key=SecretStr(SAFE_JWT_SECRET),
    )

    assert settings.api_key.get_secret_value() == SAFE_API_KEY
    assert settings.jwt_secret_key.get_secret_value() == SAFE_JWT_SECRET


def test_environment_changes_do_not_leak_between_settings(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", SAFE_API_KEY)
    monkeypatch.setenv("JWT_SECRET_KEY", SAFE_JWT_SECRET)

    production_settings = Settings(_env_file=None)

    assert production_settings.environment == "production"

    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("API_KEY", DEVELOPMENT_API_KEY)
    monkeypatch.setenv("JWT_SECRET_KEY", DEVELOPMENT_JWT_SECRET_KEY)

    test_settings = Settings(_env_file=None)

    assert test_settings.environment == "test"
    assert test_settings.api_key.get_secret_value() == DEVELOPMENT_API_KEY


@pytest.mark.parametrize(
    ("values", "match"),
    [
        (
            {
                "environment": "production",
                "jwt_secret_key": SecretStr(SAFE_JWT_SECRET),
            },
            "API_KEY.*default or placeholder",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(""),
                "jwt_secret_key": SecretStr(SAFE_JWT_SECRET),
            },
            "API_KEY.*blank",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr("   "),
                "jwt_secret_key": SecretStr(SAFE_JWT_SECRET),
            },
            "API_KEY.*blank",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(DEVELOPMENT_API_KEY),
                "jwt_secret_key": SecretStr(SAFE_JWT_SECRET),
            },
            "API_KEY.*default or placeholder",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(API_KEY_PLACEHOLDER),
                "jwt_secret_key": SecretStr(SAFE_JWT_SECRET),
            },
            "API_KEY.*default or placeholder",
        ),
    ],
)
def test_production_rejects_unsafe_api_key(
    values: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValidationError, match=match):
        build_settings(**values)


@pytest.mark.parametrize(
    ("values", "match"),
    [
        (
            {
                "environment": "production",
                "api_key": SecretStr(SAFE_API_KEY),
            },
            "JWT_SECRET_KEY.*default or placeholder",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(SAFE_API_KEY),
                "jwt_secret_key": SecretStr(""),
            },
            "JWT_SECRET_KEY.*blank",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(SAFE_API_KEY),
                "jwt_secret_key": SecretStr("   "),
            },
            "JWT_SECRET_KEY.*blank",
        ),
        (
            {
                "environment": "production",
                "api_key": SecretStr(SAFE_API_KEY),
                "jwt_secret_key": SecretStr(DEVELOPMENT_JWT_SECRET_KEY),
            },
            "JWT_SECRET_KEY.*default or placeholder",
        ),
    ],
)
def test_production_rejects_unsafe_jwt_secret(
    values: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValidationError, match=match):
        build_settings(**values)


def test_staging_rejects_unsafe_authentication_secrets() -> None:
    with pytest.raises(ValidationError, match="API_KEY.*default or placeholder"):
        build_settings(
            environment="staging",
            api_key=SecretStr(API_KEY_PLACEHOLDER),
            jwt_secret_key=SecretStr(SAFE_JWT_SECRET),
        )


def test_staging_requires_a_long_api_key() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        build_settings(
            environment="staging",
            api_key=SecretStr("too-short"),
            jwt_secret_key=SecretStr(SAFE_JWT_SECRET),
        )


def test_production_accepts_explicit_authentication_secrets() -> None:
    settings = build_settings(
        environment="production",
        api_key=SecretStr(SAFE_API_KEY),
        jwt_secret_key=SecretStr(SAFE_JWT_SECRET),
    )

    assert settings.environment == "production"


def test_production_validation_error_is_safe(monkeypatch) -> None:
    rejected_api_key = API_KEY_PLACEHOLDER
    rejected_jwt_secret = DEVELOPMENT_JWT_SECRET_KEY
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", rejected_api_key)
    monkeypatch.setenv("JWT_SECRET_KEY", rejected_jwt_secret)
    monkeypatch.setenv("UNRELATED_SECRET", UNRELATED_SECRET)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_text = str(exc_info.value)

    assert "API_KEY" in error_text
    assert "default or placeholder" in error_text
    assert rejected_api_key not in error_text
    assert rejected_jwt_secret not in error_text
    assert UNRELATED_SECRET not in error_text
    assert "/Users/" not in error_text
    assert "sre-runbook-api" not in error_text


def test_production_jwt_validation_error_is_safe(monkeypatch) -> None:
    rejected_jwt_secret = DEVELOPMENT_JWT_SECRET_KEY
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", SAFE_API_KEY)
    monkeypatch.setenv("JWT_SECRET_KEY", rejected_jwt_secret)
    monkeypatch.setenv("UNRELATED_SECRET", UNRELATED_SECRET)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_text = str(exc_info.value)

    assert "JWT_SECRET_KEY" in error_text
    assert "default or placeholder" in error_text
    assert SAFE_API_KEY not in error_text
    assert rejected_jwt_secret not in error_text
    assert UNRELATED_SECRET not in error_text
    assert "/Users/" not in error_text
    assert "sre-runbook-api" not in error_text


def test_cached_settings_refuse_unsafe_production_configuration(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", DEVELOPMENT_API_KEY)
    monkeypatch.setenv("JWT_SECRET_KEY", SAFE_JWT_SECRET)

    with pytest.raises(ValidationError, match="API_KEY.*default or placeholder"):
        get_settings()


def test_production_rejects_development_api_key() -> None:
    with pytest.raises(ValidationError, match="default or placeholder"):
        build_settings(
            environment="production",
            api_key=SecretStr(DEVELOPMENT_API_KEY),
            jwt_secret_key=SecretStr(SAFE_JWT_SECRET),
        )


def test_production_accepts_a_long_api_key() -> None:
    settings = build_settings(
        environment="production",
        api_key=SecretStr("p" * 32),
        jwt_secret_key=SecretStr("j" * 32),
    )

    assert settings.environment == "production"


def test_log_level_defaults_to_info(monkeypatch) -> None:
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = build_settings()

    assert settings.log_level == "INFO"


def test_log_level_is_case_insensitive() -> None:
    settings = build_settings(log_level="debug")

    assert settings.log_level == "DEBUG"


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        build_settings(log_level="verbose")


def test_production_rejects_development_jwt_secret(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "a" * 32)
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "development-only-jwt-secret-change-me",
    )

    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None)


def test_production_accepts_explicit_jwt_secret(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "a" * 32)
    monkeypatch.setenv("JWT_SECRET_KEY", "b" * 32)

    settings = Settings(_env_file=None)

    assert settings.environment == "production"
