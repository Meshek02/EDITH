"""FastAPI application and validated local development launcher."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api.health import router
from backend.core.config import ConfigurationError, load_settings
from backend.core.logging import configure_logging, server_log_config

VERSION = version("edith-assistant")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Validate before serving; no integrations, workers or persistence."""
    settings = load_settings()
    logger = configure_logging(settings.log_level, (settings.openai_api_key.get_secret_value(),))
    application.state.settings = settings
    logger.info("Application started")
    try:
        yield
    finally:
        logger.info("Application stopped")
        del application.state.settings


def create_app() -> FastAPI:
    """Create an app with validation at startup, including external ASGI launches."""
    application = FastAPI(
        title="EDITH",
        version=VERSION,
        description="Local backend foundation for the EDITH personal AI assistant",
        lifespan=lifespan,
        debug=False,
    )
    application.include_router(router)

    @application.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception) -> JSONResponse:
        logging.getLogger("edith").error("Unhandled application error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return application


app = create_app()


def main() -> None:
    """Honor validated host/port. External Uvicorn CLI overrides are outside this API."""
    try:
        settings = load_settings()
    except ConfigurationError as error:
        configure_logging().error(str(error))
        raise SystemExit(2) from None
    secrets = (settings.openai_api_key.get_secret_value(),)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        log_config=server_log_config(settings.log_level, secrets),
        access_log=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
