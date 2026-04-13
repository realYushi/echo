# Directory Structure

> How frontend code is organized in this project.

---

## Overview

Next.js App Router with TypeScript. Code lives in `frontend/` at the project root.

---

## Directory Layout

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Landing / entry point
│   │   └── discover/
│   │       └── page.tsx         # Split-pane discovery view
│   ├── components/
│   │   ├── ui/                  # Reusable primitives (Button, Card, Input)
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx    # Chat container (message list + input)
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ChatInput.tsx
│   │   └── recommendations/
│   │       ├── RecommendationGrid.tsx
│   │       ├── ProductCard.tsx
│   │       └── EmptyState.tsx
│   ├── hooks/
│   │   ├── useChat.ts           # Chat SSE streaming
│   │   ├── usePersona.ts        # Persona state
│   │   └── useRecommendations.ts
│   ├── lib/
│   │   ├── api.ts               # API client (fetch wrappers)
│   │   └── sse.ts               # SSE connection helper
│   ├── types/
│   │   ├── chat.ts              # Chat message types
│   │   ├── persona.ts           # Persona schema
│   │   └── product.ts           # Product schema
│   └── styles/
│       └── globals.css
├── public/
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
└── package.json
```

---

## Module Organization

- **`app/`**: Next.js routes only. Minimal logic — compose components and hooks.
- **`components/`**: Grouped by feature (`chat/`, `recommendations/`). Shared primitives in `ui/`.
- **`hooks/`**: Custom hooks. One hook per file. Named `use{Feature}.ts`.
- **`lib/`**: Non-React utilities (API clients, helpers). No React imports.
- **`types/`**: Shared TypeScript types. One file per domain object.

New features: add components under a new feature folder in `components/`, add a hook in `hooks/`, add types in `types/`.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Components | `PascalCase.tsx` | `ProductCard.tsx` |
| Hooks | `camelCase.ts` with `use` prefix | `useChat.ts` |
| Utilities | `camelCase.ts` | `api.ts` |
| Types | `camelCase.ts` | `persona.ts` |
| Directories | `kebab-case` or `camelCase` | `chat/`, `ui/` |
| CSS classes | Tailwind utilities | No custom class names unless necessary |

---

## Examples

Will be updated with links to actual files after PR5 frontend implementation.
