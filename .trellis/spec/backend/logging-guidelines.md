# Logging Guidelines

> How logging is done in this project.

---

## Overview

Use Python's `structlog` for structured JSON logging. Every log entry must include enough context to trace a request.

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

## Structured Logging

Configure `structlog` with JSON output in `main.py` lifespan:

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
)
```

Get a logger per module:

```python
logger = structlog.get_logger(__name__)
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
