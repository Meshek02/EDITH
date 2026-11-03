"""Console JSON logging with bounded, deliberately limited secret redaction."""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

_SENSITIVE = re.compile(r"api[_-]?key|password|passwd|secret|token|authorization|cookie", re.I)
_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|openai_api_key|password|passwd|secret|token|access_token|"
    r"refresh_token|authorization|cookie)\b[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[^\s,;\"']+")
_AUTH_HEADER = re.compile(r"(?i)(\b(?:authorization|cookie)\s*[:=]\s*)[^\r\n]*")
_API_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]+")


class JsonFormatter(logging.Formatter):
    """Emit an allowlist of fields; omit traceback text and arbitrary extras."""

    def __init__(self, secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.secrets = tuple(sorted((value for value in secrets if value), key=len, reverse=True))

    def redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): "[REDACTED]" if _SENSITIVE.search(str(key)) else self.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self.redact(item) for item in value]
        if not isinstance(value, str):
            return value if value is None or isinstance(value, (bool, int, float)) else "[OMITTED]"
        for secret in self.secrets:
            value = value.replace(secret, "[REDACTED]")
        value = _AUTH_HEADER.sub(r"\1[REDACTED]", value)
        value = _BEARER.sub("Bearer [REDACTED]", value)
        value = _API_KEY.sub("[REDACTED]", value)
        return _ASSIGNMENT.sub(r"\1[REDACTED]", value)

    def format(self, record: logging.LogRecord) -> str:
        message = (
            record.msg if isinstance(record.msg, dict) and not record.args else record.getMessage()
        )
        output = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": self.redact(record.name),
            "message": self.redact(message),
        }
        if isinstance(getattr(record, "fields", None), dict):
            output["fields"] = self.redact(record.fields)
        if record.exc_info and record.exc_info[0]:
            output["exception_type"] = record.exc_info[0].__name__
        return json.dumps(output, ensure_ascii=True)


def configure_logging(level: str = "INFO", secrets: tuple[str, ...] = ()) -> logging.Logger:
    """Configure only the application's logger, idempotently, without files."""
    logger = logging.getLogger("edith")
    logger.setLevel(level)
    logger.propagate = False
    owned = [handler for handler in logger.handlers if getattr(handler, "_edith_console", False)]
    if not owned:
        handler = logging.StreamHandler(sys.stderr)
        handler._edith_console = True
        logger.addHandler(handler)
        owned = [handler]
    for handler in owned:
        handler.setFormatter(JsonFormatter(secrets))
        handler.setLevel(level)
    return logger


def server_log_config(level: str, secrets: tuple[str, ...] = ()) -> dict[str, Any]:
    """Use the same formatter for server errors; disable request access logs."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "backend.core.logging.JsonFormatter", "secrets": secrets}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stderr",
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": [], "level": level, "propagate": True},
            "uvicorn.access": {"handlers": [], "level": level, "propagate": False},
        },
    }
