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
  suggestions: string[];
  replaceMessages: (messages: Message[]) => void;
  sendMessage: (content: string) => Promise<void>;
  isStreaming: boolean;
  error: string | null;
}

interface UseChatOptions {
  persona: Persona | null;
  onPersonaUpdate: (persona: Persona) => void;
  onTurnComplete?: () => Promise<void> | void;
}

export function useChat(_sessionId: string, _options: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    setError(null);
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content }]);
    // ... streaming logic
  }, []);

  return { messages, suggestions, replaceMessages, sendMessage, isStreaming, error };
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

- **Params**: `sessionId: string`, `options: { persona, onPersonaUpdate, onTurnComplete? }`
- **Returns**: `UseChatReturn { messages, suggestions, replaceMessages, sendMessage, isStreaming, error }`
- **Pattern**: Wraps `useState` + `useCallback`. Appends the user message optimistically, streams SSE events through `lib/sse.ts`, appends assistant content incrementally, processes `suggestions` events into local state, and hands persona updates back to the page coordinator.
- **Key detail**: Uses stable `Message.id` keys plus functional `setMessages((prev) => ...)` updates so streamed assistant content never closes over stale state.
- **Suggestions lifecycle**: Suggestions are cleared on new message send and on error. Reset on `sessionId` change. Set from the `suggestions` SSE event.
- **Session contract**: Reset local message/suggestion/error/streaming state on `sessionId` changes, and expose `replaceMessages()` so the page coordinator can hydrate restored history from the backend snapshot.

### useRecommendations (`src/hooks/useRecommendations.ts`)

- **Params**: `sessionId: string`
- **Returns**: `UseRecommendationsReturn { products: Recommendation[], setRecommendations, isLoading, error, refreshRecommendations }`
- **Pattern**: Owns the recommendation list, loading state, and refresh function. Calls `lib/api.ts` `fetchRecommendations()` with the `sessionId` and aborts in-flight refreshes on teardown or overlap.
- **Session contract**: Clear products/loading/error on `sessionId` changes and expose `setRecommendations()` so snapshot hydration can seed the restored shortlist.

### usePersona (`src/hooks/usePersona.ts`)

- **Params**: `sessionId: string`
- **Returns**: `UsePersonaReturn { persona, setPersona, sendFeedback, isSubmitting, error }`
- **Pattern**: Initializes with `EMPTY_PERSONA`, accepts persona snapshots from chat SSE, and sends feedback mutations through `postFeedback()`.
- **Key detail**: `sendFeedback()` is async and returns the updated persona so the page coordinator can immediately trigger a recommendation refresh.
- **Session contract**: Reset to `EMPTY_PERSONA` plus cleared error/submitting state whenever `sessionId` changes.

### useVoiceChat (`src/hooks/useVoiceChat.ts`)

- **Params**: `sessionId: string | null`, `options: { onPersonaUpdate, onRecommendationsUpdate, onFallbackToText }`
- **Returns**: `UseVoiceChatReturn { connect, disconnect, isConnected, isConnecting, error, transcripts }`
- **Pattern**: Manages Gemini Live WebSocket connection with bidirectional PCM audio streaming. Uses AudioWorklet processor (`/worklets/pcm-processor.js`) for mic capture (16kHz Int16→base64). Playback uses `AudioBufferSourceNode` scheduling at 24kHz (Int16→Float32→AudioBuffer). Fetches ephemeral tokens via `fetchVoiceToken()` before connecting. WebSocket uses `binaryType = "arraybuffer"` with synchronous `TextDecoder` for message parsing.
- **Key detail**: Transcript accumulation uses refs (`userTranscriptRef`, `assistantTranscriptRef`) flushed on `turnComplete` events, then sent to backend via `postVoiceTranscript()`. Backend persona/recommendation updates are propagated through callbacks.
- **Fallback contract**: On mic permission denied, WebSocket error, or token fetch failure, calls `onFallbackToText(reason)` with a user-friendly message and cleans up all audio/WebSocket resources.
- **Session contract**: Disconnects and resets transcripts/error state on `sessionId` changes. Cleanup on unmount closes WebSocket, stops mic tracks, and closes audio contexts.

### useSessionId (`src/hooks/useSessionId.ts`)

- **Returns**: `UseSessionIdReturn { sessionId, isReady, startNewSession }`
- **Pattern**: Persists a generated UUID in `localStorage` and exposes a `startNewSession()` helper that rotates the stored ID.
- **Key detail**: This hook stores only the session identifier. It must never cache full persona, message, or recommendation payloads in browser storage.

---

## Data Fetching

- **SSE streaming** (chat responses): `lib/sse.ts` exports `streamChat()` -- accepts a full `ChatRequest`, an `onEvent` callback typed as `(event: ChatEvent) => void`, and an optional `AbortSignal`
- **REST calls** (recommendations, feedback, restore, voice): `lib/api.ts` exports `postChat()`, `postFeedback()`, `fetchRecommendations()`, `fetchSessionSnapshot()`, `fetchVoiceToken()`, `postVoiceTranscript()`
- **No data fetching library for MVP** -- plain fetch is sufficient for the current endpoints. Add React Query if complexity grows.

**API client signatures** from `src/lib/api.ts`:
```tsx
export async function postChat(
  _request: ChatRequest,
  _signal?: AbortSignal,
): Promise<ReadableStream<Uint8Array>> { ... }

export async function postFeedback(
  _productId: string,
  _signal: FeedbackSignal,
  _sessionId: string,
): Promise<{ persona: Persona }> { ... }

export async function fetchRecommendations(
  _sessionId: string,
  _personaEmbedding?: number[],
  _signal?: AbortSignal,
): Promise<Recommendation[]> { ... }

export async function fetchSessionSnapshot(
  _sessionId: string,
  _signal?: AbortSignal,
): Promise<SessionSnapshot> { ... }

export async function fetchVoiceToken(
  _signal?: AbortSignal,
): Promise<VoiceTokenResponse> { ... }

export async function postVoiceTranscript(
  _sessionId: string,
  _messages: TranscriptMessage[],
  _signal?: AbortSignal,
): Promise<TranscriptResponse> { ... }
```

**SSE helper** from `src/lib/sse.ts`:
```tsx
export async function streamChat(
  _request: ChatRequest,
  _onEvent: (event: ChatEvent) => void,
  _signal?: AbortSignal,
): Promise<void> { ... }
```

`fetchRecommendations()` may be called with only `sessionId`; the backend recommend router will reuse the session-backed persona embedding when the explicit embedding is omitted. Keep the client and backend session contract aligned.
`fetchSessionSnapshot()` restores `messages`, `persona`, and `recommendations` for the stored session ID. Missing sessions resolve to an empty payload, not an exception status.

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
- **Don't key streamed message lists by array index** -- attach a stable `Message.id` when messages are created
- **Don't persist full server snapshots in `localStorage`** -- persist `sessionId`, then restore from the backend snapshot endpoint

---

## Reference Files

| Pattern | File |
|---------|------|
| Hook with explicit return interface | `src/hooks/useChat.ts` |
| Hook with EMPTY constant init | `src/hooks/usePersona.ts` |
| Session-backed recommendation refresh | `src/hooks/useRecommendations.ts` |
| Browser-persisted session ID | `src/hooks/useSessionId.ts` |
| Voice WebSocket + audio pipeline | `src/hooks/useVoiceChat.ts` |
| Typed API clients (fetch wrappers) | `src/lib/api.ts` |
| SSE streaming helper | `src/lib/sse.ts` |
