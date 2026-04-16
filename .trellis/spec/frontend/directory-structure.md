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
│   │   ├── layout.tsx              # Root layout (metadata, global CSS import)
│   │   ├── page.tsx                # Landing page with "Discover" CTA
│   │   └── discover/
│   │       └── page.tsx            # Split-pane discovery view ("use client")
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx              # Variant-based button primitive
│   │   │   └── CollapsibleSection.tsx  # Foldable section with chevron + aria-expanded/controls
│   │   ├── ErrorBoundary.tsx      # React error boundary with logging
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx       # Chat container (message list + input)
│   │   │   ├── MessageBubble.tsx   # Single message display (user/assistant)
│   │   │   └── ChatInput.tsx       # Text input + send button
│   │   ├── profile/
│   │   │   └── ProfileInspector.tsx    # Conversation-state inspector (persona + dev-mode raw view)
│   │   └── recommendations/
│   │       ├── RecommendationGrid.tsx  # Grid with loading/empty/populated states
│   │       ├── ProductCard.tsx     # Product display with feedback buttons
│   │       └── EmptyState.tsx      # Shown when no recommendations match
│   ├── hooks/
│   │   ├── useChat.ts             # Chat message state + SSE streaming
│   │   ├── usePersona.ts          # Persona state + feedback mutation handling
│   │   ├── useRecommendations.ts  # Session-backed recommendation refresh
│   │   └── useVoiceChat.ts        # Gemini Live WebSocket + audio capture/playback
│   ├── lib/
│   │   ├── utils.ts               # cn() helper (clsx + tailwind-merge)
│   │   ├── api.ts                 # Typed fetch clients (postChat, postFeedback, fetchRecommendations)
│   │   ├── logger.ts              # Pino logger with createLogger() factory + request ID
│   │   └── sse.ts                 # SSE stream reader + event parser
│   ├── types/
│   │   ├── chat.ts                # Message, ChatRequest, ChatEventSchema
│   │   ├── persona.ts             # PersonaSchema, FeedbackSignalSchema, EMPTY_PERSONA
│   │   ├── product.ts             # ProductSchema, RecommendationSchema
│   │   └── voice.ts               # VoiceTokenResponseSchema, TranscriptMessageSchema, TranscriptResponseSchema
│   └── styles/
│       └── globals.css            # Tailwind v4 import + body defaults
├── public/
│   └── worklets/
│       └── pcm-processor.js       # AudioWorklet for PCM capture (16kHz) + playback (24kHz)
├── next.config.ts                 # API proxy rewrites + remote image config
├── tsconfig.json                  # Strict mode, @/* path alias
├── eslint.config.mjs              # ESLint 9 flat config (next/core-web-vitals + next/typescript)
├── vitest.config.ts               # Vitest + jsdom + @/ alias
├── postcss.config.mjs             # Tailwind v4 via @tailwindcss/postcss plugin
├── .prettierrc                    # Semi, double quotes, trailing commas, tailwind plugin
└── package.json                   # Scripts: dev, build, lint, test, typecheck
```

---

## Module Organization

- **`app/`**: Next.js routes only. Minimal logic -- compose components and hooks. See `src/app/discover/page.tsx` for the pattern: `"use client"` directive, hook calls, layout JSX.
- **`components/`**: Grouped by feature (`chat/`, `recommendations/`). Shared primitives in `ui/`. Every component uses named exports.
- **`hooks/`**: Custom hooks. One hook per file. Named `use{Feature}.ts`. Each defines an explicit return interface (`UseChatReturn`, `UseRecommendationsReturn`, etc.).
- **`lib/`**: Non-React utilities (API clients, helpers, logger). No React imports. `api.ts` owns fetch + Zod validation at the API boundary; `sse.ts` owns stream decoding and event parsing; `logger.ts` owns structured logging via Pino with child loggers per module.
- **`types/`**: Shared TypeScript types. One file per domain object. Zod schemas live here alongside inferred types, and chat messages include stable `id` fields for streamed rendering.

New features: add components under a new feature folder in `components/`, add a hook in `hooks/`, add types in `types/`.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Components | `PascalCase.tsx` | `ProductCard.tsx` |
| Hooks | `camelCase.ts` with `use` prefix | `useChat.ts` |
| Utilities | `camelCase.ts` | `api.ts`, `utils.ts` |
| Types | `camelCase.ts` | `persona.ts` |
| Directories | `kebab-case` or `camelCase` | `chat/`, `ui/` |
| CSS classes | Tailwind utilities | No custom class names unless necessary |

---

## Key Config Files

**Path alias** (`tsconfig.json:21-23`):
```json
"paths": {
  "@/*": ["./src/*"]
}
```

**API proxy** (`next.config.ts:4-10`):
```ts
images: {
  remotePatterns: [{ protocol: "https", hostname: "placehold.co" }],
},

async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://localhost:8000/api/:path*",
    },
  ];
}
```

**Tailwind v4** (`postcss.config.mjs`):
```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

**Tailwind entry** (`src/styles/globals.css`):
```css
@import "tailwindcss";
```

Note: Tailwind v4 uses `@import "tailwindcss"` instead of the v3 `@tailwind base/components/utilities` directives. There is no `tailwind.config.ts` -- Tailwind v4 uses CSS-based configuration.

---

## Examples

| What | File |
|------|------|
| Root layout with metadata and global CSS | `src/app/layout.tsx` |
| Landing page with CTA link | `src/app/page.tsx` |
| Split-pane state coordinator | `src/app/discover/page.tsx` |
| Variant-based UI primitive | `src/components/ui/Button.tsx` |
| Feature component group | `src/components/chat/` |
| Domain types with Zod | `src/types/product.ts` |
| Typed API clients | `src/lib/api.ts` |
