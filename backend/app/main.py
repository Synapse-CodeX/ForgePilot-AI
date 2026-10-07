import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

settings = get_settings()

configure_logging()

logger = logging.getLogger("forgepilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""

    logger.info("Starting %s", settings.app_name)

    yield

    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=("Autonomous repository debugging and repair agent."),
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(
    health_router,
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
