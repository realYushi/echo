# Error Handling

> How errors are handled in this project.

---

## Overview

FastAPI exception handlers convert all errors to a consistent JSON envelope. Services raise typed exceptions; routers never catch-and-swallow.

---

## Error Types

Define custom exceptions in `app/exceptions.py`:

```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)

class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)

class ExternalServiceError(AppError):
    def __init__(self, service: str, message: str):
        super().__init__(f"{service}: {message}", "EXTERNAL_ERROR", 502)
```

| Exception | When to use |
|-----------|------------|
| `NotFoundError` | Session or product not found |
| `ValidationError` | Business rule violation (not input parsing — Pydantic handles that) |
| `ExternalServiceError` | Claude API, Qdrant, or CLIP failures |

---

## Error Handling Patterns

### Services raise, routers don't catch

```python
# Service — raise on failure
async def get_persona(session_id: str) -> Persona:
    checkpoint = await get_checkpoint(session, session_id)
    if not checkpoint:
        raise NotFoundError(f"Session {session_id} not found")
    return checkpoint.persona

# Router — let the global handler deal with it
@router.post("/api/chat")
async def chat(request: ChatRequest):
    persona = await persona_service.get_persona(request.session_id)
    ...
```

### Claude API failures: graceful degradation

The chat endpoint must remain usable if Claude is down. Catch `ExternalServiceError` in the SSE streaming loop and send a fallback message to the client instead of dropping the connection.

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

## API Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Session abc123 not found"
  }
}
```

Register a global exception handler in `main.py`:

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
```

Pydantic validation errors are handled by FastAPI's built-in handler (returns 422 with field-level details).

---

## Common Mistakes

- **Don't return error details from external services to the client** — log the full error, return a generic message.
- **Don't use bare `except Exception`** without re-raising or converting to a typed error.
- **Don't mix HTTP status codes with business logic** — services raise domain exceptions, the handler maps to HTTP status.
