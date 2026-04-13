# Hook Guidelines

> How hooks are used in this project.

---

## Overview

Custom hooks encapsulate all data fetching, SSE streaming, and complex state logic. Components call hooks; hooks call `lib/` utilities.

---

## Custom Hook Patterns

One hook per concern. Hooks return typed objects, not arrays.

```tsx
// Good: clear return type
function useChat(sessionId: string) {
  return {
    messages,
    sendMessage,
    isStreaming,
    error,
  };
}

// Bad: positional returns (ambiguous)
function useChat(sessionId: string) {
  return [messages, sendMessage, isStreaming]; // Which is which?
}
```

Hooks that manage async operations should expose: `data`, `isLoading`, `error`.

---

## Data Fetching

- **SSE streaming** (chat responses): Custom hook using `EventSource` or fetch + `ReadableStream` in `lib/sse.ts`
- **REST calls** (recommendations, feedback): `fetch` wrappers in `lib/api.ts`
- **No data fetching library for MVP** — plain fetch is sufficient for 3 endpoints. Add React Query if complexity grows.

```tsx
// lib/api.ts — typed fetch wrapper
export async function postFeedback(productId: string, signal: "like" | "dislike"): Promise<FeedbackResponse> {
  const res = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ productId, signal }),
  });
  if (!res.ok) throw new ApiError(res.status, await res.json());
  return res.json();
}
```

SSE pattern for chat streaming:

```tsx
function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  async function sendMessage(content: string) {
    setIsStreaming(true);
    // Append user message immediately
    setMessages((prev) => [...prev, { role: "user", content }]);

    // Stream assistant response via SSE
    const stream = await streamChat(sessionId, content);
    // ... accumulate tokens, update messages
    setIsStreaming(false);
  }

  return { messages, sendMessage, isStreaming };
}
```

---

## Naming Conventions

- File: `use{Feature}.ts` — `useChat.ts`, `usePersona.ts`
- Hook function: `use{Feature}` — must start with `use`
- Location: `src/hooks/` (shared) or co-located if only used by one component

---

## Common Mistakes

- **Don't fetch inside `useEffect` without cleanup** — cancel in-flight requests on unmount
- **Don't create hooks that are just wrappers around `useState`** — that adds indirection with no value
- **Don't call hooks conditionally** — React rules of hooks apply
- **Don't forget to handle the SSE connection teardown** — close `EventSource` / abort `ReadableStream` on unmount
