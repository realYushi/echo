# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

Python type hints are mandatory. Ruff for linting and formatting. Pytest for testing.

---

## Forbidden Patterns

| Pattern | Why | Instead |
|---------|-----|---------|
| `# type: ignore` without explanation | Hides real type issues | Fix the type or add a comment explaining why |
| `from typing import Any` as a default | Defeats type checking | Use proper types, `Protocol`, or generics |
| Mutable default arguments | Shared state bugs | Use `None` and assign in function body |
| `import *` | Pollutes namespace, breaks static analysis | Explicit imports |
| Sync blocking calls in async functions | Blocks event loop | Use `asyncio.to_thread()` or async libraries |
| Global mutable state | Hard to test, race conditions | Inject via FastAPI dependencies |

---

## Required Patterns

- **Type hints on all function signatures** — parameters and return types
- **Pydantic models** for all API request/response schemas
- **`pydantic-settings`** for configuration (not raw `os.getenv`)
- **Async** for all I/O-bound operations (DB, HTTP, Qdrant)
- **Dependency injection** via FastAPI's `Depends()` for DB sessions, clients, settings

---

## Testing Requirements

- **Framework**: pytest + pytest-asyncio + httpx (for `AsyncClient`)
- **Coverage target**: Core services (persona, recommendation) must have tests. Routers tested via integration tests.
- **Test naming**: `test_{function_name}_{scenario}` → `test_extract_persona_empty_messages`
- **Fixtures**: Shared fixtures in `conftest.py`. Use factory functions over static fixtures.
- **Mocking**: Mock external services (Claude API, Qdrant) at the client boundary, not inside services.

```python
# Good: mock the HTTP client
async def test_persona_extraction(mock_claude_client):
    mock_claude_client.messages.create.return_value = ...
    result = await extract_persona(messages, client=mock_claude_client)
    assert result.style_preferences == ["modern"]

# Bad: mock internal functions
@patch("app.services.persona._call_claude")  # Too tightly coupled
```

---

## Code Review Checklist

- [ ] Type hints on all functions
- [ ] No `Any` types without justification
- [ ] Async used for I/O operations
- [ ] Errors raise typed exceptions (not bare `raise Exception`)
- [ ] New endpoints have corresponding schema models
- [ ] Tests cover the happy path and at least one error case

---

## Tooling

- **Linter/formatter**: Ruff (`ruff check` + `ruff format`)
- **Type checker**: mypy (strict mode)
- **Test runner**: pytest
- **Config**: All in `pyproject.toml`
