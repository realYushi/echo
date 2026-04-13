from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.dependencies import get_settings
from app.exceptions import AppError
from app.routers import chat, feedback, recommend

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

    return app


app = create_app()
