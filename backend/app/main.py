from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from qdrant_client import AsyncQdrantClient

from app.dependencies import get_settings
from app.exceptions import AppError
from app.routers import chat, feedback, recommend, session, voice
from app.services.catalog import seed_catalog

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from app.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure structlog and run startup/shutdown tasks."""
    settings: Settings = get_settings()

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(processors=processors)

    logger = structlog.get_logger(__name__)
    await logger.ainfo("application_startup", debug=settings.debug)

    # Seed product catalog into Qdrant
    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        count = await seed_catalog(qdrant, settings.qdrant_collection)
        await logger.ainfo("catalog_seeded", product_count=count)
    finally:
        await qdrant.close()

    yield

    await logger.ainfo("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Echo Backend", version="0.1.0", lifespan=lifespan)

    settings = get_settings()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger = structlog.get_logger("request")
        start = time.perf_counter()
        await logger.ainfo("request_started", method=request.method, path=request.url.path)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        await logger.ainfo(
            "request_finished",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # Global exception handler for AppError hierarchy
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    # Include routers with /api prefix
    app.include_router(chat.router, prefix="/api")
    app.include_router(recommend.router, prefix="/api")
    app.include_router(feedback.router, prefix="/api")
    app.include_router(session.router, prefix="/api")
    app.include_router(voice.router, prefix="/api")

    return app


app = create_app()
