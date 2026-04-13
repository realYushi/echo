# Cross-Layer Thinking Guide

> **Purpose**: Think through data flow across layers before implementing.

---

## The Problem

**Most bugs happen at layer boundaries**, not within layers.

Common cross-layer bugs:
- API returns format A, frontend expects format B
- Database stores X, service transforms to Y, but loses data
- Multiple layers implement the same logic differently

---

## Before Implementing Cross-Layer Features

### Step 1: Map the Data Flow

Draw out how data moves:

```
Source → Transform → Store → Retrieve → Transform → Display
```

For each arrow, ask:
- What format is the data in?
- What could go wrong?
- Who is responsible for validation?

### Step 2: Identify Boundaries

| Boundary | Common Issues |
|----------|---------------|
| API ↔ Service | Type mismatches, missing fields |
| Service ↔ Database | Format conversions, null handling |
| Backend ↔ Frontend | Serialization, date formats |
| Component ↔ Component | Props shape changes |

### Step 3: Define Contracts

For each boundary:
- What is the exact input format?
- What is the exact output format?
- What errors can occur?

---

## Common Cross-Layer Mistakes

### Mistake 1: Implicit Format Assumptions

**Bad**: Assuming date format without checking

**Good**: Explicit format conversion at boundaries

### Mistake 2: Scattered Validation

**Bad**: Validating the same thing in multiple layers

**Good**: Validate once at the entry point

### Mistake 3: Leaky Abstractions

**Bad**: Component knows about database schema

**Good**: Each layer only knows its neighbors

### Mistake 4: snake_case / camelCase Mismatch

**Bad**: Returning backend snake_case directly to frontend, or manually renaming fields in each endpoint.

**Good**: Use a shared `CamelModel` base class with `alias_generator=to_camel` + `populate_by_name=True`. All API-facing schemas inherit from it. Use `model_dump(by_alias=True)` for manual serialization (SSE events, dict returns). See `app/schemas/base.py`.

### Mistake 5: TYPE_CHECKING vs Runtime at API Boundary

**Bad**: Putting FastAPI endpoint signature types under `if TYPE_CHECKING:` when `from __future__ import annotations` is active. Pydantic + FastAPI resolve annotations at runtime for schema generation -- forward refs fail.

**Good**: Import request body types, `Settings`, and DI client types at runtime in router files, with `# noqa: TC001` / `# noqa: TC002` to suppress ruff. See `app/routers/chat.py`.

---

## Checklist for Cross-Layer Features

Before implementation:
- [ ] Mapped the complete data flow
- [ ] Identified all layer boundaries
- [ ] Defined format at each boundary
- [ ] Decided where validation happens
- [ ] Confirmed snake_case/camelCase serialization strategy (CamelModel + `by_alias=True`)
- [ ] Router endpoint signature types are imported at runtime (not under TYPE_CHECKING)

After implementation:
- [ ] Tested with edge cases (null, empty, invalid)
- [ ] Verified error handling at each boundary
- [ ] Checked data survives round-trip
- [ ] Verified API responses use camelCase keys

---

## When to Create Flow Documentation

Create detailed flow docs when:
- Feature spans 3+ layers
- Multiple teams are involved
- Data format is complex
- Feature has caused bugs before
