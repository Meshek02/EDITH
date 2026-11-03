"""Deterministic status only; no external connections or execution."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Public allowlist of non-sensitive backend status fields."""

    assistant: str
    version: str
    status: Literal["healthy"] = "healthy"
    ai_connected: Literal[False] = False
    windows_control_enabled: Literal[False] = False


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(
        assistant=request.app.state.settings.name,
        version=request.app.version,
    )
