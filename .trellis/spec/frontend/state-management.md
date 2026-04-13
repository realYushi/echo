# State Management

> How state is managed in this project.

---

## Overview

Lightweight state approach for MVP. React's built-in primitives (`useState`, `useRef`, prop drilling) cover most needs. The app has one main view (discovery split-pane) with two coordinated panels.

---

## State Categories

| Category | Where it lives | Examples |
|----------|---------------|----------|
| **Component state** | `useState` in the component | Input field value, hover state, UI toggles |
| **Feature state** | Custom hooks | Chat messages, persona, recommendations |
| **Shared state** | Props passed from page component | Session ID, persona (shared between chat and recommendations) |
| **Server state** | Backend (PostgreSQL/Qdrant) | Checkpoints, product catalog |

---

## When to Use Global State

**For MVP: avoid global state stores.** The discovery page is the only view with complex state, and it can be managed by lifting state to the page component and passing down via props.

```tsx
// discover/page.tsx — state coordinator
export default function DiscoverPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const chat = useChat(sessionId);
  const persona = usePersona(chat.latestPersona);
  const recommendations = useRecommendations(persona.embedding);

  return (
    <SplitPane>
      <ChatPanel {...chat} />
      <RecommendationGrid
        products={recommendations.products}
        onFeedback={chat.sendFeedback}
      />
    </SplitPane>
  );
}
```

Introduce Zustand or Context only if:
- 3+ levels of prop drilling for the same data
- Multiple unrelated components need the same state
- Neither applies in MVP scope

---

## Server State

- Server is the source of truth for: persona, recommendations, chat history (via checkpoints)
- Client holds a local copy that updates via SSE stream and REST responses
- On page refresh: re-fetch from server using session ID (checkpoint restore)
- Don't cache server state in `localStorage` — the backend checkpoint handles persistence

---

## Common Mistakes

- **Don't reach for Context/Zustand by default** — prop drilling 1-2 levels is fine and more explicit
- **Don't duplicate server state in client stores** — fetch from backend, hold in hook state
- **Don't sync state between panels via events** — lift state to the shared parent instead
- **Don't store derived values in state** — compute them during render

```tsx
// Bad: derived state in useState
const [filteredProducts, setFilteredProducts] = useState([]);
useEffect(() => {
  setFilteredProducts(products.filter(...));
}, [products]);

// Good: compute during render
const filteredProducts = products.filter(...);
```
