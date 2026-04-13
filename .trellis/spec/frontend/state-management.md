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

The `src/app/discover/page.tsx` is the state coordinator. It restores or creates the session ID, hydrates server-backed state, calls the hooks, and passes data down to the two panels via props.

**Actual implementation** from `src/app/discover/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useChat } from "@/hooks/useChat";
import { usePersona } from "@/hooks/usePersona";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useSessionId } from "@/hooks/useSessionId";
import { fetchSessionSnapshot } from "@/lib/api";
import { EMPTY_PERSONA } from "@/types/persona";

export default function DiscoverPage() {
  const { sessionId } = useSessionId();
  const [isHydrating, setIsHydrating] = useState(false);
  const resolvedSessionId = sessionId ?? "";
  const persona = usePersona(resolvedSessionId);
  const recommendations = useRecommendations(resolvedSessionId);
  const chat = useChat(resolvedSessionId, {
    persona: persona.persona,
    onPersonaUpdate: persona.setPersona,
    onTurnComplete: async () => {
      await recommendations.refreshRecommendations();
    },
  });
  const replaceMessages = chat.replaceMessages;
  const setPersona = persona.setPersona;
  const setRecommendations = recommendations.setRecommendations;

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const controller = new AbortController();
    setIsHydrating(true);

    void fetchSessionSnapshot(sessionId, controller.signal)
      .then((snapshot) => {
        replaceMessages(/* map snapshot.messages -> Message[] */);
        setPersona(snapshot.persona ?? EMPTY_PERSONA);
        setRecommendations(snapshot.recommendations);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsHydrating(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [replaceMessages, setPersona, setRecommendations, sessionId]);
}
```

Key details:
- `useSessionId()` persists only the session identifier in `localStorage`; it must not persist messages, persona, or recommendations
- Hydration fetches `GET /api/sessions/{sessionId}` on first load and after `startNewSession()` rotates to a fresh ID
- Each hook owns its slice of state (`chat` owns messages/streaming, `persona` owns the taste profile, `recommendations` owns products/loading)
- Hooks must clear their local state when `sessionId` changes so a newly generated session never shows stale restored data
- Data flows down via props: `chat.messages` -> `ChatPanel`, `recommendations.products` -> `RecommendationGrid`
- The page coordinates cross-hook effects: snapshot restore seeds local state; chat turn completes -> refresh recommendations; feedback saves persona -> refresh recommendations

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
- Cache only the session identifier in `localStorage`; restore the actual workspace state from `/api/sessions/{sessionId}`
- If snapshot hydration fails, reset local chat/persona/recommendation state and show a restore error instead of leaving mixed old state on screen

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
| Session ID persistence | `src/hooks/useSessionId.ts` |
| Component-local state (input) | `src/components/chat/ChatInput.tsx` |
