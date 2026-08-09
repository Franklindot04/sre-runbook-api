from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_API_KEY = "development-only-change-me"
DEVELOPMENT_JWT_SECRET_KEY = "development-only-jwt-secret-change-me"
API_KEY_PLACEHOLDERS = frozenset(
    {
        DEVELOPMENT_API_KEY,
        "replace-with-a-long-random-secret",
    }
)
JWT_SECRET_KEY_PLACEHOLDERS = frozenset({DEVELOPMENT_JWT_SECRET_KEY})
PRODUCTION_ENVIRONMENTS = frozenset({"production", "staging"})


class Settings(BaseSettings):
    app_name: str = "SRE Runbook API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///./sre_runbook.db"
    api_key: SecretStr = SecretStr(DEVELOPMENT_API_KEY)
    api_key_header: str = "X-API-Key"
    jwt_secret_key: SecretStr = SecretStr(DEVELOPMENT_JWT_SECRET_KEY)
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_logging_configuration(self) -> "Settings":
        valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        self.log_level = self.log_level.upper()
        if self.log_level not in valid_levels:
            raise ValueError(
                "LOG_LEVEL must be one of: "
                + ", ".join(sorted(valid_levels))
            )
        return self

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        environment = self.environment.lower()

        if environment in PRODUCTION_ENVIRONMENTS:
            self._validate_production_secret(
                setting_name="API_KEY",
                secret=self.api_key,
                unsafe_values=API_KEY_PLACEHOLDERS,
            )
            self._validate_production_secret(
                setting_name="JWT_SECRET_KEY",
                secret=self.jwt_secret_key,
                unsafe_values=JWT_SECRET_KEY_PLACEHOLDERS,
            )

            key = self.api_key.get_secret_value()
            if len(key) < 32:
                raise ValueError(
                    "API_KEY must contain at least 32 characters outside development."
                )

            jwt_key = self.jwt_secret_key.get_secret_value()
            if len(jwt_key) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must contain at least 32 characters "
                    "outside development."
                )

        return self

    @staticmethod
    def _validate_production_secret(
        *,
        setting_name: str,
        secret: SecretStr,
        unsafe_values: frozenset[str],
    ) -> None:
        value = secret.get_secret_value()
        if not value.strip():
            raise ValueError(
                f"{setting_name} must not be blank outside development."
            )

        if value in unsafe_values:
            raise ValueError(
                f"{setting_name} must not use a repository default or "
                "placeholder outside development."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
