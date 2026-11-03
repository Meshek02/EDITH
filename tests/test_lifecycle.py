"""Startup validation, lifecycle logging and launcher configuration."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.core.config import ConfigurationError
from backend.main import create_app, main


def test_startup_shutdown(capsys: pytest.CaptureFixture[str]) -> None:
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert hasattr(app.state, "settings")
    assert not hasattr(app.state, "settings")
    messages = [json.loads(line)["message"] for line in capsys.readouterr().err.splitlines()]
    assert messages == ["Application started", "Application stopped"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("EDITH_AI_ENABLED", "true"),
        ("EDITH_WINDOWS_CONTROL_ENABLED", "true"),
        ("EDITH_REMOTE_ACCESS_ENABLED", "true"),
        ("EDITH_HOST", "0.0.0.0"),
    ],
)
def test_startup_fails_before_serving(
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: str,
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ConfigurationError), TestClient(create_app()):
        pytest.fail("Forbidden configuration reached serving state")


def test_launcher_honors_validated_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    import uvicorn

    calls = []
    monkeypatch.setenv("EDITH_PORT", "8125")
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    main()
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8125
    assert calls[0]["access_log"] is False
    assert calls[0]["proxy_headers"] is False


def test_launcher_rejects_unsafe_host(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import uvicorn

    monkeypatch.setenv("EDITH_HOST", "0.0.0.0")
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: pytest.fail("Server must not launch"))
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 2
    assert "Invalid Phase 1 configuration" in capsys.readouterr().err
