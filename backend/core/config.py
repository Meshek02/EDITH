"""Validated local-only Phase 1 configuration."""

from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(ValueError):
    """Invalid configuration, reported without echoing input values."""


class Settings(BaseSettings):
    """Load process variables and optional .env from the working directory."""

    model_config = SettingsConfigDict(
        env_prefix="EDITH_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    name: str = Field(default="EDITH", min_length=1, max_length=100)
    env: Literal["development", "test", "production"] = "development"
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    ai_enabled: bool = False
    windows_control_enabled: bool = False
    remote_access_enabled: bool = False
    local_ai_provider: Literal["ollama"] = "ollama"
    cloud_ai_provider: Literal["openai"] = "openai"
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434", validation_alias="OLLAMA_BASE_URL"
    )
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="OPENAI_API_KEY",
        repr=False,
        exclude=True,
    )
    database_url: str = Field(default="sqlite:///./data/edith.db", repr=False)

    @field_validator("ai_enabled", "windows_control_enabled", "remote_access_enabled")
    @classmethod
    def reject_enabled_features(cls, value: bool) -> bool:
        if value:
            raise ValueError("Feature must remain disabled in Phase 1")
        return value


def load_settings() -> Settings:
    """Fail closed with field names only; never render raw validation inputs."""
    try:
        return Settings()
    except ValidationError as error:
        fields = sorted({str(item["loc"][0]) for item in error.errors(include_input=False)})
        raise ConfigurationError("Invalid Phase 1 configuration: " + ", ".join(fields)) from None
