# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

Python backend using **FastAPI** (async), **SQLAlchemy** (async ORM) + **Alembic** (migrations) for PostgreSQL, and **Qdrant** for vector search. LLM orchestration via **LangGraph** with **Claude** as the LLM.

---

## Pre-Development Checklist

Before writing backend code, read the guidelines relevant to your task:

1. **Always read**: [Directory Structure](./directory-structure.md) — know where files go
2. **If touching DB or Qdrant**: [Database Guidelines](./database-guidelines.md)
3. **If adding/modifying endpoints**: [Error Handling](./error-handling.md)
4. **If adding observability**: [Logging Guidelines](./logging-guidelines.md)
5. **Before committing**: [Quality Guidelines](./quality-guidelines.md) — checklist at the bottom

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled (lightweight) |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | Filled (lightweight) |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Filled (lightweight) |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled (lightweight) |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | Filled (lightweight) |

---

## Quick Reference

- **Language**: Python 3.12+
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy (async) + Alembic
- **Vector DB**: Qdrant
- **LLM**: Claude via Anthropic SDK
- **Agent**: LangGraph
- **Linter**: Ruff
- **Type checker**: mypy (strict)
- **Tests**: pytest + pytest-asyncio

---

**Language**: All documentation should be written in **English**.
