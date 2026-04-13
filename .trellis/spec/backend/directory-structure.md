# Directory Structure

> How backend code is organized in this project.

---

## Overview

Python backend using FastAPI. Code lives in `backend/` at the project root.

---

## Directory Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory (create_app), lifespan, global error handler
│   ├── config.py            # Settings via pydantic-settings (env vars)
│   ├── dependencies.py      # Shared FastAPI dependencies (get_settings, get_db_session, get_qdrant_client)
│   ├── exceptions.py        # AppError hierarchy (NotFoundError, ValidationError, ExternalServiceError)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py          # POST /api/chat (SSE streaming)
│   │   ├── recommend.py     # POST /api/recommend
│   │   └── feedback.py      # POST /api/feedback
│   ├── services/
│   │   ├── __init__.py
│   │   ├── persona.py       # Persona extraction + embedding (extract_persona, embed_persona)
│   │   ├── recommendation.py # Qdrant retrieval + scoring (get_recommendations)
│   │   ├── catalog.py       # Product catalog operations (seed_catalog, get_product)
│   │   └── session.py       # In-memory session store (get_session, save_session)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py         # LangGraph 6-node agent definition (build_graph)
│   │   ├── nodes.py         # Individual node implementations (greet, discover, extract_persona, ...)
│   │   └── state.py         # AgentState TypedDict
│   ├── models/
│   │   └── __init__.py      # SQLAlchemy models (empty -- add models here when needed)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py          # CamelModel base class (camelCase alias_generator)
│   │   ├── chat.py          # ChatRequest
│   │   ├── persona.py       # Persona
│   │   └── product.py       # Product, Recommendation, FeedbackRequest, RecommendRequest
│   ├── data/
│   │   ├── __init__.py
│   │   └── products.py      # Seed data (SEED_PRODUCTS list of Product instances)
│   └── utils/
│       ├── __init__.py
│       └── embeddings.py    # CLIP embedding helpers (get_clip_embedding)
├── tests/
│   ├── __init__.py
│   └── conftest.py          # Shared fixtures (sample_messages)
├── alembic/
│   ├── env.py               # Async Alembic setup (reads Settings for DB URL)
│   ├── script.py.mako
│   └── versions/
│       └── .gitkeep
├── alembic.ini
├── pyproject.toml
├── .env.example
└── Dockerfile
```

---

## Module Organization

- **Routers**: Thin -- validate input via schema, call service, return response. No business logic.
- **Services**: All business logic. Services call other services, never routers.
- **Agent**: LangGraph-specific code. The graph definition (`graph.py`) and node implementations (`nodes.py`). Agent state is a `TypedDict` defined in `state.py`.
- **Models**: SQLAlchemy ORM models. One file per table or closely related group. Currently empty -- add models here when LangGraph checkpoints or other persistence is needed.
- **Schemas**: Pydantic models for API request/response and internal data transfer.
- **Data**: Static seed data and constants. Exports typed lists of Pydantic models (e.g., `SEED_PRODUCTS`).
- **Utils**: Stateless helper functions. No dependencies on services or models.
- **Dependencies**: FastAPI `Depends()` providers for settings, DB session, and Qdrant client. Shared across all routers.

New features: add a router + service + schema files. Don't create new top-level directories.

---

## Naming Conventions

- Files: `snake_case.py`
- Directories: `snake_case/`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Router files match the API resource: `/api/chat` -> `routers/chat.py`
- Schema files match the domain object: persona -> `schemas/persona.py`

---

## Key Patterns

### App Factory (`app/main.py`)

The application uses a factory function `create_app()` that returns a configured `FastAPI` instance. A module-level `app = create_app()` is the ASGI entry point.

```python
# app/main.py:47-78
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Echo Backend", version="0.1.0", lifespan=lifespan)

    settings = get_settings()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        ...
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
```

### Router Registration

All routers are included with `prefix="/api"` in `create_app()`. Each router file creates its own `router = APIRouter()` and defines endpoints without the `/api` prefix (the prefix is applied at registration time).

### Dependency Injection (`app/dependencies.py`)

Three shared dependencies, all using `Depends()`:

- `get_settings()` -- cached with `@lru_cache(maxsize=1)`, returns `Settings`
- `get_db_session()` -- yields `AsyncSession`, one per request
- `get_qdrant_client()` -- returns `AsyncQdrantClient`
- `get_anthropic_client()` -- returns `AsyncAnthropic | None` (None when API key is empty)

### `from __future__ import annotations`

Every Python file in the codebase starts with `from __future__ import annotations` for PEP 604 style unions and deferred type evaluation. Follow this pattern in all new files.

### TYPE_CHECKING Guards

Runtime-unnecessary imports (used only for type hints) are placed under `if TYPE_CHECKING:` blocks. This is the standard pattern across all files.

**Exception -- FastAPI endpoint signatures**: Types used in `@router` endpoint function signatures (request body, `Annotated[..., Depends(...)]` parameters) must be imported at runtime because FastAPI + Pydantic resolve annotations at runtime for schema generation. Use `# noqa: TC001` or `# noqa: TC002` to suppress the ruff lint rule.

```python
# app/routers/chat.py -- correct pattern for router files
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from anthropic import AsyncAnthropic  # noqa: TC002 - FastAPI resolves at runtime
from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient  # noqa: TC002 - FastAPI resolves at runtime

from app.config import Settings  # noqa: TC001 - FastAPI resolves at runtime
from app.schemas.chat import ChatRequest  # noqa: TC001 - FastAPI resolves at runtime

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator  # OK under TYPE_CHECKING -- not in endpoint signature
```

---

## Examples

| Pattern | File |
|---------|------|
| App factory + lifespan + error handler | `app/main.py` |
| Pydantic settings with env file | `app/config.py` |
| Dependency injection (lru_cache, async generator) | `app/dependencies.py` |
| Exception hierarchy | `app/exceptions.py` |
| Router with SSE streaming + DI | `app/routers/chat.py` |
| Router with schema input/output + DI | `app/routers/recommend.py` |
| Router with error propagation + DI | `app/routers/feedback.py` |
| CamelModel base for API serialization | `app/schemas/base.py` |
| Pydantic schema with Optional fields | `app/schemas/persona.py` |
| Pydantic schema with Literal type | `app/schemas/product.py` |
| In-memory session store | `app/services/session.py` |
| AgentState TypedDict | `app/agent/state.py` |
| LangGraph node signatures | `app/agent/nodes.py` |
| Async Alembic env | `alembic/env.py` |
| Test fixture | `tests/conftest.py` |
