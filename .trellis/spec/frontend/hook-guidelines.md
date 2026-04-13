# Hook Guidelines

> How hooks are used in this project.

---

## Overview

Custom hooks encapsulate all data fetching, SSE streaming, and complex state logic. Components call hooks; hooks call `lib/` utilities. Each hook defines an explicit return type interface.

---

## Custom Hook Patterns

One hook per concern. Hooks return typed objects (not arrays). Every hook defines a `Use{Feature}Return` interface.

**Actual pattern** from `src/hooks/useChat.ts`:

```tsx
interface UseChatReturn {
  messages: Message[];
  sendMessage: (content: string) => void;
  isStreaming: boolean;
  error: string | null;
}

export function useChat(_sessionId: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback((content: string) => {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);
    // ... streaming logic
  }, []);

  return { messages, sendMessage, isStreaming, error };
}
```

**Anti-pattern** -- do not use positional returns:
```tsx
// Bad: positional returns (ambiguous)
function useChat(sessionId: string) {
  return [messages, sendMessage, isStreaming]; // Which is which?
}
```

---

## Existing Hooks

### useChat (`src/hooks/useChat.ts`)

- **Params**: `sessionId: string`
- **Returns**: `UseChatReturn { messages, sendMessage, isStreaming, error }`
- **Pattern**: Wraps `useState` + `useCallback`. Appends user message optimistically, then triggers assistant response. Currently uses a `setTimeout` placeholder -- will wire to `lib/sse.ts` `streamChat()` in a later PR.
- **Key detail**: Uses functional `setMessages((prev) => [...prev, newMsg])` to avoid stale closure over messages array.

### useRecommendations (`src/hooks/useRecommendations.ts`)

- **Params**: `sessionId: string`
- **Returns**: `UseRecommendationsReturn { products: Recommendation[], isLoading, error }`
- **Pattern**: Stub that returns empty arrays. Will call `lib/api.ts` `fetchRecommendations()` when persona has >= 2 signals.

### usePersona (`src/hooks/usePersona.ts`)

- **Params**: none
- **Returns**: `UsePersonaReturn { persona: Persona, addSignal }`
- **Pattern**: Initializes with `EMPTY_PERSONA` constant from `src/types/persona.ts`. `addSignal` accepts `{ productId, signal }` and updates approvals/rejections arrays. Will be wired to backend `postFeedback()` in a later PR.
- **Key detail**: Defines a local `PersonaSignal` interface for the signal parameter.

---

## Data Fetching

- **SSE streaming** (chat responses): `lib/sse.ts` exports `streamChat()` -- accepts sessionId, message, and an `onEvent` callback typed as `(event: ChatEvent) => void`
- **REST calls** (recommendations, feedback): `lib/api.ts` exports `postChat()`, `postFeedback()`, `fetchRecommendations()`
- **No data fetching library for MVP** -- plain fetch is sufficient for 3 endpoints. Add React Query if complexity grows.

**API client stubs** from `src/lib/api.ts`:
```tsx
export async function postChat(
  _request: ChatRequest,
): Promise<ReadableStream<Uint8Array>> { ... }

export async function postFeedback(
  _productId: string,
  _signal: FeedbackSignal,
  _sessionId: string,
): Promise<{ persona: Persona }> { ... }

export async function fetchRecommendations(
  _sessionId: string,
  _personaEmbedding: number[],
): Promise<Recommendation[]> { ... }
```

**SSE helper stub** from `src/lib/sse.ts`:
```tsx
export async function streamChat(
  _sessionId: string,
  _message: string,
  _onEvent: (event: ChatEvent) => void,
): Promise<void> { ... }
```

Both `api.ts` and `sse.ts` currently throw `NotImplementedError`. When implementing, replace the throw with real fetch/SSE logic. The function signatures (params and return types) are the contract -- do not change them without updating all call sites.

---

## Hook Implementation Conventions

- Prefix unused parameters with `_` (e.g., `_sessionId`) to signal "not yet wired"
- Use `useCallback` for functions returned from hooks to maintain stable references (see `useChat.ts:18`, `usePersona.ts:20`)
- Use functional state updates `setState((prev) => ...)` when the new state depends on previous state
- Expose `error: string | null` for hooks that involve async operations

---

## Naming Conventions

- File: `use{Feature}.ts` -- `useChat.ts`, `usePersona.ts`, `useRecommendations.ts`
- Hook function: `use{Feature}` -- must start with `use`
- Return interface: `Use{Feature}Return`
- Location: `src/hooks/` (shared) or co-located if only used by one component

---

## Common Mistakes

- **Don't fetch inside `useEffect` without cleanup** -- cancel in-flight requests on unmount
- **Don't create hooks that are just wrappers around `useState`** -- that adds indirection with no value
- **Don't call hooks conditionally** -- React rules of hooks apply
- **Don't forget to handle the SSE connection teardown** -- close `EventSource` / abort `ReadableStream` on unmount
- **Don't close over stale state in callbacks** -- use functional `setState` or `useCallback` with proper deps

---

## Reference Files

| Pattern | File |
|---------|------|
| Hook with explicit return interface | `src/hooks/useChat.ts` |
| Hook with EMPTY constant init | `src/hooks/usePersona.ts` |
| Hook stub returning empty state | `src/hooks/useRecommendations.ts` |
| API client stubs (fetch wrappers) | `src/lib/api.ts` |
| SSE streaming helper | `src/lib/sse.ts` |
