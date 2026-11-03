"""Isolate tests from local configuration, credentials and logger handlers."""

import logging
import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    for name in list(os.environ):
        if name.upper().startswith("EDITH_") or name.upper() in {
            "OPENAI_API_KEY",
            "OLLAMA_BASE_URL",
        }:
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    logger = logging.getLogger("edith")
    handlers, level, propagate = logger.handlers[:], logger.level, logger.propagate
    logger.handlers = []
    yield
    for handler in logger.handlers:
        handler.close()
    logger.handlers = handlers
    logger.setLevel(level)
    logger.propagate = propagate
