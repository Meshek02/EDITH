"""Settings validation exercises real environment and dotenv sources."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.config import ConfigurationError, Settings, load_settings


def test_secure_defaults_without_dotenv() -> None:
    settings = load_settings()
    assert settings.name == "EDITH"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.env == "development"
    assert settings.log_level == "INFO"
    assert not settings.ai_enabled
    assert not settings.windows_control_enabled
    assert not settings.remote_access_enabled
    assert settings.openai_api_key.get_secret_value() == ""
    assert not Path(".env").exists()


@pytest.mark.parametrize("port", [1, 8000, 65535])
def test_valid_ports(port: int) -> None:
    assert Settings(port=port).port == port


@pytest.mark.parametrize("port", [0, -1, 65536, "invalid", "1.5"])
def test_invalid_ports(port: object) -> None:
    with pytest.raises(ValidationError):
        Settings(port=port)


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "8.8.8.8", "::", "::1", "localhost"])
def test_only_supported_loopback_host(host: str) -> None:
    with pytest.raises(ValidationError):
        Settings(host=host)


@pytest.mark.parametrize("key,value", [("log_level", "TRACE"), ("env", "staging"), ("name", "")])
def test_invalid_settings(key: str, value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(**{key: value})


@pytest.mark.parametrize("key", ["AI", "WINDOWS_CONTROL", "REMOTE_ACCESS"])
@pytest.mark.parametrize("value", ["true", "1", "yes", "on"])
def test_forbidden_feature_environment(
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: str,
) -> None:
    monkeypatch.setenv(f"EDITH_{key}_ENABLED", value)
    with pytest.raises(ConfigurationError, match="Invalid Phase 1 configuration"):
        load_settings()


@pytest.mark.parametrize("value", ["false", "0", "no", "off"])
def test_false_boolean_parsing(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("EDITH_AI_ENABLED", value)
    assert load_settings().ai_enabled is False


def test_dotenv_and_environment_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    Path(".env").write_text("EDITH_NAME=Friday\nEDITH_PORT=8123\nOPENAI_API_KEY=\n")
    monkeypatch.setenv("EDITH_PORT", "8124")
    settings = load_settings()
    assert settings.name == "Friday"
    assert settings.port == 8124
    assert settings.openai_api_key.get_secret_value() == ""


def test_secret_is_not_repr_or_serialized(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-only-credential-not-real"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    settings = load_settings()
    assert secret not in repr(settings)
    assert secret not in settings.model_dump_json()
    monkeypatch.setenv("EDITH_PORT", secret)
    with pytest.raises(ConfigurationError) as raised:
        load_settings()
    assert secret not in str(raised.value)
    assert "port" in str(raised.value)


def test_invalid_dotenv_cannot_enable_remote_access() -> None:
    Path(".env").write_text("EDITH_REMOTE_ACCESS_ENABLED=true\n")
    with pytest.raises(ConfigurationError):
        load_settings()


def test_settings_are_immutable() -> None:
    with pytest.raises(ValidationError):
        Settings().ai_enabled = True
