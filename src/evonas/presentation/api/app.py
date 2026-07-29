"""FastAPI application factory — EvoNAS control plane (Phase 9)."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evonas import __version__
from evonas.application.platform.container import get_container
from evonas.infrastructure.logging.setup import setup_logging
from evonas.presentation.api.middleware import RequestLogMiddleware
from evonas.presentation.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    container = get_container()
    setup_logging(
        level=container.settings.log_level,
        json_logs=container.settings.json_logs,
    )
    container.events.bind_loop(asyncio.get_running_loop())
    logger.info("EvoNAS API v%s starting (%s)", __version__, container.settings.environment)
    yield
    container.shutdown()
    logger.info("EvoNAS API shutdown")


def create_app() -> FastAPI:
    """Build the FastAPI application with DI-backed routes."""
    container = get_container()
    settings = container.settings
    app = FastAPI(
        title=settings.title,
        version=__version__,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLogMiddleware)
    app.include_router(router)

    @app.get("/", tags=["root"])
    def root() -> dict[str, Any]:
        return {
            "name": "EvoNAS",
            "version": __version__,
            "docs": settings.docs_url,
            "health": "/api/v1/health",
        }

    return app


# ASGI entry for uvicorn: `uvicorn evonas.presentation.api.app:app`
app = create_app()
