"""Representative redaction checks; no claim of universal secret detection."""

import json
import logging
from datetime import datetime
from pathlib import Path

import pytest

from backend.core.logging import JsonFormatter, configure_logging


def test_fields_severity_and_no_duplicate_handlers(capsys: pytest.CaptureFixture[str]) -> None:
    logger = configure_logging()
    configure_logging()
    assert len(logger.handlers) == 1
    assert not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
    logger.warning("Verification message")
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert set(record) == {"timestamp", "level", "logger", "message"}
    assert datetime.fromisoformat(record["timestamp"]).tzinfo is not None
    assert record["level"] == "WARNING"
    assert record["logger"] == "edith"
    assert record["message"] == "Verification message"
    assert not list(Path.cwd().glob("*.log"))


@pytest.mark.parametrize(
    "message,secret",
    [
        ("OPENAI_API_KEY=sk-test-only-123", "sk-test-only-123"),
        ("Authorization: Bearer test-token-123", "test-token-123"),
        ("Authorization: Basic test-basic-123", "test-basic-123"),
        ("password=test-password-123", "test-password-123"),
        ('token="test token with spaces"', "test token with spaces"),
        ("Credential is configured-test-secret", "configured-test-secret"),
    ],
)
def test_string_redaction(message: str, secret: str) -> None:
    formatter = JsonFormatter(("configured-test-secret",))
    record = logging.LogRecord("edith", logging.INFO, "", 0, "%s", (message,), None)
    output = formatter.format(record)
    assert secret not in output
    assert "[REDACTED]" in output


def test_nested_fields_and_exception_redaction() -> None:
    record = logging.LogRecord(
        "edith",
        logging.ERROR,
        "",
        0,
        {
            "event": "test",
            "api_key": "test-key",
            "nested": [{"password": "test-pass"}],
        },
        (),
        None,
    )
    record.fields = {"Authorization": "Bearer test-auth", "token": "test-token"}
    try:
        raise ValueError("test-exception-secret")
    except ValueError:
        import sys

        record.exc_info = sys.exc_info()
    output = JsonFormatter().format(record)
    for value in ["test-key", "test-pass", "test-auth", "test-token", "test-exception-secret"]:
        assert value not in output
    assert json.loads(output)["exception_type"] == "ValueError"
