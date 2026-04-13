# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

**Next.js 15** (App Router) with **TypeScript** (strict mode), **React 19**, and **Tailwind CSS v4**. The main UI is a split-pane discovery view with chat on the left and product recommendations on the right.

---

## Pre-Development Checklist

Before writing frontend code, read the guidelines relevant to your task:

1. **Always read**: [Directory Structure](./directory-structure.md) -- know where files go
2. **If building components**: [Component Guidelines](./component-guidelines.md)
3. **If adding hooks or data fetching**: [Hook Guidelines](./hook-guidelines.md)
4. **If managing state**: [State Management](./state-management.md)
5. **If defining types or validating data**: [Type Safety](./type-safety.md)
6. **Before committing**: [Quality Guidelines](./quality-guidelines.md) -- checklist at the bottom

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | Filled |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | Filled |
| [State Management](./state-management.md) | Local state, global state, server state | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled |
| [Type Safety](./type-safety.md) | Type patterns, validation | Filled |

---

## Quick Reference

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.8 (strict)
- **Styling**: Tailwind CSS v4 (via `@tailwindcss/postcss`)
- **Validation**: Zod 3.24 (at API boundary)
- **Linter**: ESLint 9 (flat config) + Prettier 3
- **Tests**: Vitest 3 + React Testing Library 16
- **Path alias**: `@/*` maps to `./src/*` (tsconfig.json)
- **API proxy**: Next.js rewrites `/api/:path*` to `http://localhost:8000/api/:path*` (next.config.ts)

---

**Language**: All documentation should be written in **English**.
