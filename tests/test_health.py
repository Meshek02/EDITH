"""Health and API safety tests, with no live network dependencies."""

import socket
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


def test_health_schema_and_no_sensitive_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDITH_NAME", "Friday")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-secret")

    def forbidden_connection(*args: object, **kwargs: object) -> None:
        pytest.fail("Health/lifecycle attempted a network connection")

    with TestClient(create_app()) as client:
        # Windows creates loopback sockets for its event loop before requests.
        monkeypatch.setattr(socket.socket, "connect", forbidden_connection)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json() == {
            "assistant": "Friday",
            "version": version("edith-assistant"),
            "status": "healthy",
            "ai_connected": False,
            "windows_control_enabled": False,
        }
        assert "test-only-secret" not in response.text
        schema = client.get("/openapi.json").json()
        assert set(schema["paths"]) == {"/health"}
        assert "HealthResponse" in schema["components"]["schemas"]


def test_only_health_and_framework_routes_no_cors() -> None:
    app = create_app()
    assert {route.path for route in app.routes if hasattr(route, "path")} == {
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
    assert set(app.openapi()["paths"]) == {"/health"}
    assert app.debug is False
    assert not app.user_middleware
    with TestClient(app) as client:
        response = client.get("/health", headers={"Origin": "https://example.com"})
        assert "access-control-allow-origin" not in response.headers
        assert client.post("/health").status_code == 405
        assert client.post("/execute", json={"command": "anything"}).status_code == 404


def test_unhandled_errors_do_not_leak_tracebacks() -> None:
    app = create_app()

    @app.get("/test-error", include_in_schema=False)
    def error_route() -> None:
        raise RuntimeError("test-only-private-detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "test-only-private-detail" not in response.text
