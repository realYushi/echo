# State Management

> How state is managed in this project.

---

## Overview

Lightweight state approach for MVP. React's built-in primitives (`useState`, `useCallback`, prop drilling) cover all needs. The app has one main view (discovery split-pane) with two coordinated panels.

---

## State Categories

| Category | Where it lives | Examples |
|----------|---------------|----------|
| **Component state** | `useState` in the component | Input field value (`ChatInput.tsx:12`), UI toggles |
| **Feature state** | Custom hooks | Chat messages (`useChat.ts`), persona (`usePersona.ts`), recommendations (`useRecommendations.ts`) |
| **Shared state** | Props passed from page component | Session ID, messages, isStreaming, products (passed from `discover/page.tsx` to children) |
| **Server state** | Backend (PostgreSQL/Qdrant) | Checkpoints, product catalog |

---

## State Coordination Pattern

The `src/app/discover/page.tsx` is the state coordinator. It creates the session, calls the hooks, and passes data down to the two panels via props.

**Actual implementation** from `src/app/discover/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { RecommendationGrid } from "@/components/recommendations/RecommendationGrid";
import { useChat } from "@/hooks/useChat";
import { usePersona } from "@/hooks/usePersona";
import { useRecommendations } from "@/hooks/useRecommendations";

export default function DiscoverPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const persona = usePersona(sessionId);
  const recommendations = useRecommendations(sessionId);
  const chat = useChat(sessionId, {
    persona: persona.persona,
    onPersonaUpdate: persona.setPersona,
    onTurnComplete: async () => {
      await recommendations.refreshRecommendations();
    },
  });

  return (
    <RecommendationGrid
      products={recommendations.products}
      onFeedback={async (productId, signal) => {
        const updatedPersona = await persona.sendFeedback(productId, signal);
        if (updatedPersona) {
          await recommendations.refreshRecommendations();
        }
      }}
      isLoading={recommendations.isLoading}
      isFeedbackPending={persona.isSubmitting}
      error={persona.error ?? recommendations.error}
      emptyTitle="Your shortlist will appear here"
      emptyDescription="Start the conversation on the left."
    />
  );
}
```

Key details:
- `sessionId` is created once via `useState(() => crypto.randomUUID())` -- the lazy initializer ensures it stays stable across re-renders
- Each hook owns its slice of state (`chat` owns messages/streaming, `persona` owns the taste profile, `recommendations` owns products/loading)
- Data flows down via props: `chat.messages` -> `ChatPanel`, `recommendations.products` -> `RecommendationGrid`
- The page coordinates cross-hook effects: chat turn completes -> refresh recommendations; feedback saves persona -> refresh recommendations

---

## When to Use Global State

**For MVP: avoid global state stores.** The discovery page is the only view with complex state, and it is managed by lifting state to the page component and passing down via props.

Introduce Zustand or Context only if:
- 3+ levels of prop drilling for the same data
- Multiple unrelated components need the same state
- Neither applies in MVP scope

---

## Server State

- Server is the source of truth for: persona, recommendations, chat history (via LangGraph checkpoints)
- Client holds a local copy that updates via SSE stream and REST responses
- Recommendation refreshes can use `sessionId` alone because the backend reuses the server-stored persona embedding for that session
- On page refresh: re-fetch from server using session ID (checkpoint restore)
- Don't cache server state in `localStorage` -- the backend checkpoint handles persistence

---

## Common Mistakes

- **Don't reach for Context/Zustand by default** -- prop drilling 1-2 levels is fine and more explicit
- **Don't duplicate server state in client stores** -- fetch from backend, hold in hook state
- **Don't sync state between panels via events** -- lift state to `discover/page.tsx` instead
- **Don't store derived values in state** -- compute them during render

```tsx
// Bad: derived state in useState
const [filteredProducts, setFilteredProducts] = useState([]);
useEffect(() => {
  setFilteredProducts(products.filter(...));
}, [products]);

// Good: compute during render
const filteredProducts = products.filter(...);
```

---

## Reference Files

| Pattern | File |
|---------|------|
| State coordinator (page-level) | `src/app/discover/page.tsx` |
| Feature state hook (chat) | `src/hooks/useChat.ts` |
| Feature state hook (persona) | `src/hooks/usePersona.ts` |
| Feature state hook (recommendations) | `src/hooks/useRecommendations.ts` |
| Component-local state (input) | `src/components/chat/ChatInput.tsx` |
