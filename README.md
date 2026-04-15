# Echo

Product discovery chatbot that extracts user preferences from conversation and generates real-time product recommendations using vector search.

## Architecture

```
User  ←→  Next.js (frontend)  ←→  FastAPI (backend)
                                       ├── LangGraph agent (Claude)
                                       ├── Qdrant (vector search)
                                       ├── PostgreSQL (persistence)
                                       └── Gemini Live API (voice)
```

**Backend** — Python 3.12, FastAPI (async), SQLAlchemy + Alembic, Qdrant, LangGraph with Claude, CLIP embeddings

**Frontend** — Next.js 15 (App Router), React 19, TypeScript (strict), Tailwind CSS v4

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- Anthropic API key
- Gemini API key (for voice mode)

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL on port 5432 and Qdrant on port 6333.

### 2. Backend

```bash
cd backend
cp .env.example .env          # fill in API keys
pip install -e ".[dev]"       # or: uv pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:3000/discover

### Run checks

```bash
make lint    # ruff + mypy (backend), eslint (frontend)
make test    # pytest (backend), vitest (frontend)
```

## Key Features

- **Chat-based discovery** — conversational UI that extracts taste signals in real time
- **Persona extraction** — LangGraph agent builds a structured preference profile (likes, dislikes, budget tier)
- **Vector recommendations** — CLIP embeddings + Qdrant similarity search, refreshed each turn
- **Feedback loop** — like/dislike on recommendations feeds back into the persona
- **Voice mode** — real-time voice conversation via Gemini Live API with text fallback

## Project Structure

```
backend/
  app/
    agent/        LangGraph graph, nodes, state
    routers/      FastAPI route handlers
    schemas/      Pydantic request/response models
    services/     Business logic (persona, catalog, recommendation, voice)
    models/       SQLAlchemy ORM models
    utils/        Embeddings, shared utilities
  alembic/        Database migrations
  tests/          pytest test suite

frontend/
  src/
    app/          Next.js pages and layout
    components/   React components (chat, recommendations, UI)
    hooks/        Custom React hooks
    lib/          API client, utilities
    types/        TypeScript type definitions
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for required configuration.
