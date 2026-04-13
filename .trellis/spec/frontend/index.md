# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

**Next.js** (App Router) with **TypeScript** (strict mode), **React**, and **Tailwind CSS**. The main UI is a split-pane discovery view with chat on the left and product recommendations on the right.

---

## Pre-Development Checklist

Before writing frontend code, read the guidelines relevant to your task:

1. **Always read**: [Directory Structure](./directory-structure.md) — know where files go
2. **If building components**: [Component Guidelines](./component-guidelines.md)
3. **If adding hooks or data fetching**: [Hook Guidelines](./hook-guidelines.md)
4. **If managing state**: [State Management](./state-management.md)
5. **If defining types or validating data**: [Type Safety](./type-safety.md)
6. **Before committing**: [Quality Guidelines](./quality-guidelines.md) — checklist at the bottom

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled (lightweight) |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | Filled (lightweight) |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | Filled (lightweight) |
| [State Management](./state-management.md) | Local state, global state, server state | Filled (lightweight) |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled (lightweight) |
| [Type Safety](./type-safety.md) | Type patterns, validation | Filled (lightweight) |

---

## Quick Reference

- **Framework**: Next.js (App Router)
- **Language**: TypeScript (strict)
- **Styling**: Tailwind CSS
- **Validation**: Zod (at API boundary)
- **Linter**: ESLint + Prettier
- **Tests**: Vitest + React Testing Library

---

**Language**: All documentation should be written in **English**.
