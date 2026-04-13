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
│   ├── main.py              # FastAPI app factory, middleware, lifespan
│   ├── config.py            # Settings via pydantic-settings (env vars)
│   ├── dependencies.py      # Shared FastAPI dependencies (DB session, Qdrant client)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py          # POST /api/chat (SSE streaming)
│   │   ├── recommend.py     # POST /api/recommend
│   │   └── feedback.py      # POST /api/feedback
│   ├── services/
│   │   ├── __init__.py
│   │   ├── persona.py       # Persona extraction + embedding
│   │   ├── recommendation.py # Qdrant retrieval + scoring
│   │   └── catalog.py       # Product catalog operations
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py         # LangGraph 6-node agent definition
│   │   ├── nodes.py         # Individual node implementations
│   │   └── state.py         # Agent state schema
│   ├── models/
│   │   ├── __init__.py
│   │   └── checkpoint.py    # SQLAlchemy models (LangGraph checkpoints)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py          # Request/response Pydantic models
│   │   ├── persona.py       # Persona schema
│   │   └── product.py       # Product schema
│   └── utils/
│       ├── __init__.py
│       └── embeddings.py    # CLIP embedding helpers
├── tests/
│   ├── conftest.py
│   ├── test_routers/
│   └── test_services/
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── pyproject.toml
└── Dockerfile
```

---

## Module Organization

- **Routers**: Thin — validate input, call service, return response. No business logic.
- **Services**: All business logic. Services call other services, never routers.
- **Agent**: LangGraph-specific code. The graph definition and node implementations.
- **Models**: SQLAlchemy ORM models. One file per table or closely related group.
- **Schemas**: Pydantic models for API request/response and internal data transfer.
- **Utils**: Stateless helper functions. No dependencies on services or models.

New features: add a router + service + schema files. Don't create new top-level directories.

---

## Naming Conventions

- Files: `snake_case.py`
- Directories: `snake_case/`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Router files match the API resource: `/api/chat` → `routers/chat.py`
- Schema files match the domain object: persona → `schemas/persona.py`

---

## Examples

Will be updated with links to actual files after PR1 scaffolding.
