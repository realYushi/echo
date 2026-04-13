# Logging Guidelines

> How logging is done in this project.

---

## Overview

Use Python's `structlog` for structured JSON logging. Every log entry must include enough context to trace a request.

---

## Setup

Structlog is configured in the application lifespan function in `app/main.py`:

```python
# app/main.py:22-44
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
```

Key details:
- `settings.debug` (from `app/config.py`) controls the renderer: `ConsoleRenderer` for dev, `JSONRenderer` for prod
- The `DEBUG` env var controls `settings.debug` (see `.env.example`)
- `contextvars.merge_contextvars` enables request-scoped context binding
- Async logging methods (`ainfo`, `adebug`, etc.) are used in the lifespan

---

## Log Levels

| Level | Use for | Example |
|-------|---------|---------|
| `DEBUG` | Internal state useful during development | Persona JSON after extraction |
| `INFO` | Normal operations worth tracking | "Chat session started", "Recommendations served" |
| `WARNING` | Recoverable issues | Qdrant returned 0 results, Claude response was slow |
| `ERROR` | Failures requiring attention | Claude API error, database connection lost |

Default level: `INFO` in production, `DEBUG` in development.

---

## Usage Pattern

Get a logger per module:

```python
import structlog

logger = structlog.get_logger(__name__)
```

Use async log methods in async functions:

```python
await logger.ainfo("application_startup", debug=settings.debug)
```

Bind request context in middleware:

```python
structlog.contextvars.bind_contextvars(request_id=request_id, session_id=session_id)
```

---

## What to Log

- **INFO**: Session creation, chat message received, recommendations served, feedback recorded
- **WARNING**: Empty Qdrant results, slow LLM responses (>5s), retry attempts
- **ERROR**: All exceptions before they become HTTP responses
- **DEBUG**: Persona JSON snapshots, embedding vectors (truncated), Qdrant query params

Always include: `session_id`, `request_id`, operation name.

---

## What NOT to Log

- Full chat message content (user privacy)
- API keys or tokens
- Full embedding vectors at INFO level (too large)
- Pydantic model dumps containing user input at INFO level

When logging user-adjacent data at DEBUG level, truncate to reasonable lengths.

---

## Examples

| Pattern | File |
|---------|------|
| Structlog configuration (lifespan) | `app/main.py:22-44` |
| Async logging with context (`ainfo`) | `app/main.py:40-41` |
