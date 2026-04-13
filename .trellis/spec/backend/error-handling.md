# Error Handling

> How errors are handled in this project.

---

## Overview

FastAPI exception handlers convert all errors to a consistent JSON envelope. Services raise typed exceptions; routers never catch-and-swallow.

---

## Error Types

Custom exceptions are defined in `app/exceptions.py`:

```python
# app/exceptions.py:4-33
class AppError(Exception):
    """Base application error with structured error info."""

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(AppError):
    """Business rule violation (422). Not for input parsing -- Pydantic handles that."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR", 422)


class ExternalServiceError(AppError):
    """External service failure (502). Use for Claude API, Qdrant, or CLIP failures."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(f"{service}: {message}", "EXTERNAL_ERROR", 502)
```

| Exception | When to use |
|-----------|------------|
| `NotFoundError` | Session or product not found |
| `ValidationError` | Business rule violation (not input parsing -- Pydantic handles that) |
| `ExternalServiceError` | Claude API, Qdrant, or CLIP failures. Pass the service name as first arg. |

### Adding New Error Types

Subclass `AppError` with a fixed `code` and `status_code`. Follow the existing pattern:

```python
class RateLimitError(AppError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(message, "RATE_LIMIT", 429)
```

---

## Global Error Handler

The global exception handler is registered in `create_app()` inside `app/main.py`:

```python
# app/main.py:63-68
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
```

This catches all `AppError` subclasses automatically. All error responses follow this format:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Session abc123 not found"
  }
}
```

Pydantic validation errors are handled by FastAPI's built-in handler (returns 422 with field-level details).

---

## Error Handling Patterns

### Services raise, routers don't catch

Routers are thin. Services raise typed exceptions, and the global handler converts them to HTTP responses.

```python
# Service -- raise on failure
async def get_persona(session_id: str) -> Persona:
    checkpoint = await get_checkpoint(session, session_id)
    if not checkpoint:
        raise NotFoundError(f"Session {session_id} not found")
    return checkpoint.persona

# Router -- let the global handler deal with it
@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    persona = await persona_service.get_persona(request.session_id)
    ...
```

### Claude API failures: graceful degradation

The chat endpoint must remain usable if Claude is down. Catch `ExternalServiceError` in the SSE streaming loop and send a fallback message to the client instead of dropping the connection.

```python
# app/routers/chat.py -- SSE error handling pattern
try:
    result = await run_agent_turn(state, ...)
except Exception as exc:
    await logger.aerror("chat_agent_turn_failed", session_id=session_id, error=str(exc))
    yield _sse_event({"type": "error", "message": "Something went wrong. Please try again."})
    yield _sse_event({"type": "done"})
    return
```

This is the one approved exception to the "services raise, routers don't catch" rule. The SSE stream must always terminate with a `done` event so the frontend can clean up.

### Never swallow exceptions silently

```python
# Bad
try:
    result = await call_external()
except Exception:
    pass  # Lost forever

# Good
try:
    result = await call_external()
except Exception:
    logger.exception("external call failed")
    raise ExternalServiceError("claude", "API call failed")
```

---

## Common Mistakes

- **Don't return error details from external services to the client** -- log the full error, return a generic message.
- **Don't use bare `except Exception`** without re-raising or converting to a typed error.
- **Don't mix HTTP status codes with business logic** -- services raise domain exceptions, the handler maps to HTTP status.
- **Don't forget `-> None` return type hint on `__init__`** -- the existing exceptions include this (see `app/exceptions.py`), follow the pattern.

---

## Examples

| Pattern | File |
|---------|------|
| Full exception hierarchy | `app/exceptions.py` |
| Global error handler registration | `app/main.py:63-68` |
| Router that lets errors propagate | `app/routers/feedback.py` |
| SSE error handling (catch + emit error event) | `app/routers/chat.py` |
