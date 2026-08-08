from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_API_KEY = "development-only-change-me"


class Settings(BaseSettings):
    app_name: str = "SRE Runbook API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///./sre_runbook.db"
    api_key: SecretStr = SecretStr(DEVELOPMENT_API_KEY)
    api_key_header: str = "X-API-Key"

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
        production_environments = {"production", "staging"}
        environment = self.environment.lower()
        key = self.api_key.get_secret_value()

        if environment in production_environments:
            if key == DEVELOPMENT_API_KEY:
                raise ValueError(
                    "API_KEY must be explicitly configured outside development."
                )

            if len(key) < 32:
                raise ValueError(
                    "API_KEY must contain at least 32 characters outside development."
                )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
