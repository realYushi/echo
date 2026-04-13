# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

Python type hints are mandatory. Ruff for linting and formatting. Pytest for testing. All configuration lives in `pyproject.toml`.

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
| Missing `from __future__ import annotations` | Inconsistent with codebase convention | Add as first import in every file |
| Runtime imports used only for type hints | Unnecessary runtime cost | Put under `if TYPE_CHECKING:` block |
| Endpoint signature types under `TYPE_CHECKING` | FastAPI + Pydantic can't resolve forward refs for schema generation | Import at runtime with `# noqa: TC001` / `# noqa: TC002` |

---

## Required Patterns

- **`from __future__ import annotations`** as the first import in every file (see all files in `app/`)
- **Type hints on all function signatures** -- parameters and return types
- **`-> None` return type** on `__init__` methods (see `app/exceptions.py`)
- **Pydantic models** for all API request/response schemas (see `app/schemas/`)
- **`pydantic-settings`** for configuration, not raw `os.getenv` (see `app/config.py`)
- **Async** for all I/O-bound operations (DB, HTTP, Qdrant)
- **Dependency injection** via FastAPI's `Depends()` for DB sessions, clients, settings (see `app/dependencies.py`)
- **`TYPE_CHECKING` guards** for imports used only in type hints (see `app/services/persona.py`)
- **Exception**: Imports used in FastAPI endpoint signatures (request body types, `Annotated[..., Depends()]` types) must be at runtime with `# noqa: TC001` / `# noqa: TC002` (see `app/routers/chat.py`)
- **`Annotated` types** for dependency injection parameters (see `app/dependencies.py:33-34`)

### Actual Code Examples

Settings with pydantic-settings (`app/config.py`):

```python
# app/config.py:1-17
from __future__ import annotations

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/echo"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"
    anthropic_api_key: str = ""
    clip_model: str = "ViT-B-32"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

Dependency injection with `Annotated` and `Depends` (`app/dependencies.py`):

```python
# app/dependencies.py:16-19
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
```

```python
# app/dependencies.py:33-39
async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session. One session per request."""
    factory = _get_session_factory(settings.database_url)
    async with factory() as session:
        yield session
```

Pydantic schema with `Literal` type (`app/schemas/product.py`):

```python
# app/schemas/product.py:28-30
class FeedbackRequest(BaseModel):
    """User feedback on a recommended product."""

    product_id: str
    signal: Literal["like", "dislike"]
```

Pydantic schema with Optional fields (`app/schemas/persona.py`):

```python
# app/schemas/persona.py:6-16
class Persona(CamelModel):
    """User taste persona extracted from conversation signals."""

    project_type: str | None = None
    budget_tier: str | None = None
    role: str | None = None
    style_preferences: list[str] = []
    material_preferences: list[str] = []
    categories: list[str] = []
    rejections: list[str] = []
    approvals: list[str] = []
```

CamelModel base for API boundary serialization (`app/schemas/base.py`):

```python
# app/schemas/base.py:1-14
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """Base model that accepts and emits camelCase at the API boundary."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

All API-facing schemas inherit from `CamelModel`. Use `model_dump(by_alias=True)` when serializing responses manually (e.g., inside SSE events or dict returns). FastAPI auto-serializes by alias for Pydantic response models.

Thread-safe lazy singleton for heavy models (`app/utils/embeddings.py`):

```python
# app/utils/embeddings.py:17-39
_model: torch.nn.Module | None = None
_tokenizer: Any = None
_lock = threading.Lock()

def _load_model() -> tuple[torch.nn.Module, Any]:
    global _model, _tokenizer  # noqa: PLW0603
    if _model is None or _tokenizer is None:
        with _lock:
            if _model is None or _tokenizer is None:  # double-check after lock
                _model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", ...)
                _model.eval()
                _tokenizer = open_clip.get_tokenizer("ViT-B-32")
    return _model, _tokenizer
```

Wrapping sync inference in `asyncio.to_thread()` (`app/utils/embeddings.py`):

```python
# app/utils/embeddings.py:42-65
def _encode_text_sync(text: str) -> list[float]:
    """Synchronous — run via asyncio.to_thread()."""
    model, tokenizer = _load_model()
    tokens = tokenizer([text])
    with torch.no_grad():
        text_features = model.encode_text(tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
    return text_features[0].tolist()

async def get_clip_embedding(text: str) -> list[float]:
    return await asyncio.to_thread(_encode_text_sync, text)
```

Agent state as `TypedDict` (`app/agent/state.py`):

```python
# app/agent/state.py:10-15
class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    persona: Persona | None
    persona_embedding: list[float]
    recommendations: list[Recommendation]
    session_id: str
```

Router pattern -- thin handler with DI and SSE streaming (`app/routers/chat.py`):

```python
# app/routers/chat.py:81-92
router = APIRouter()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    anthropic_client: Annotated[AsyncAnthropic | None, Depends(get_anthropic_client)],
) -> StreamingResponse:
    """Stream chat responses via SSE."""
    return StreamingResponse(
        _chat_stream(request, settings, qdrant_client, anthropic_client),
        media_type="text/event-stream",
    )
```

---

## Testing Requirements

- **Framework**: pytest + pytest-asyncio + httpx (for `AsyncClient`)
- **Config**: `asyncio_mode = "auto"` in `pyproject.toml` -- no need for `@pytest.mark.asyncio`
- **Test paths**: `tests/` directory (configured in `pyproject.toml`)
- **Coverage target**: Core services (persona, recommendation) must have tests. Routers tested via integration tests.
- **Test naming**: `test_{function_name}_{scenario}` -- e.g., `test_extract_persona_empty_messages`
- **Fixtures**: Shared fixtures in `tests/conftest.py`. Use factory functions over static fixtures.
- **Mocking**: Mock external services (Claude API, Qdrant) at the client boundary, not inside services.

Existing fixture example (`tests/conftest.py`):

```python
# tests/conftest.py:6-12
@pytest.fixture
def sample_messages() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "I'm renovating my kitchen"},
        {"role": "assistant", "content": "What style are you going for?"},
        {"role": "user", "content": "Modern minimalist, white and wood tones"},
    ]
```

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

## Tooling Configuration

All tooling is configured in `pyproject.toml`:

### Ruff (`pyproject.toml:38-43`)

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM", "TCH"]
```

Rule sets: pycodestyle (E/W), pyflakes (F), isort (I), pep8-naming (N), pyupgrade (UP), flake8-bugbear (B), flake8-builtins (A), flake8-simplify (SIM), flake8-type-checking (TCH).

Commands:
- `ruff check app/ tests/` -- lint
- `ruff format app/ tests/` -- format
- `ruff check --fix app/ tests/` -- auto-fix

### mypy (`pyproject.toml:45-57`)

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
plugins = ["pydantic.mypy"]
```

Command: `mypy app/`

### pytest (`pyproject.toml:59-61`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Command: `pytest`

---

## Code Review Checklist

- [ ] `from __future__ import annotations` at top of file
- [ ] Type hints on all functions (params + return)
- [ ] No `Any` types without justification
- [ ] Async used for I/O operations
- [ ] Errors raise typed exceptions from `app/exceptions.py` (not bare `raise Exception`)
- [ ] New endpoints have corresponding schema models in `app/schemas/`
- [ ] Runtime-only imports used; type-hint-only imports under `if TYPE_CHECKING:`
- [ ] Tests cover the happy path and at least one error case
- [ ] `ruff check` passes
- [ ] `mypy app/` passes
