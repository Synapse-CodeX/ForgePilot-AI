"""FastAPI application entry point for ForgePilot AI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import configure_logging

settings = get_settings()

configure_logging()

logger = logging.getLogger("forgepilot")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""

    logger.info("Starting %s", settings.app_name)

    yield

    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="Autonomous repository debugging and repair agent.",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(
    api_router,
    prefix=settings.api_prefix,
)


@app.get("/")
async def root() -> dict[str, str]:
    """Return basic application information."""

    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
    }
