# Type Safety

> Type safety patterns in this project.

---

## Overview

TypeScript strict mode (`tsconfig.json:8`). No `any` types. Shared types in `src/types/`. Zod for runtime validation of API responses.

---

## Type Organization

- **`src/types/`**: Domain types shared across components and hooks. One file per domain.
- **Component-local types**: `interface {Component}Props` in the component file.
- **Hook return types**: `interface Use{Feature}Return` in the hook file.
- **API response types**: Defined in `src/types/`, validated with Zod at the API boundary.

Actual layout:
```
src/types/
├── chat.ts       # Message, ChatRequest, ChatEvent
├── persona.ts    # Persona, FeedbackSignal, EMPTY_PERSONA
└── product.ts    # ProductSchema (Zod), Product, Recommendation
```

Types mirror the backend Pydantic schemas. Keep them in sync manually for MVP; share via codegen if drift becomes a problem.

---

## Actual Type Definitions

### Message and Chat types (`src/types/chat.ts`)

```tsx
import { z } from "zod";
import { PersonaSchema, type Persona } from "./persona";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  sessionId: string;
  message: string;
  persona: Persona | null;
}

export const ChatEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("token"), content: z.string() }),
  z.object({ type: z.literal("persona_update"), persona: PersonaSchema }),
  z.object({ type: z.literal("done") }),
  z.object({ type: z.literal("error"), message: z.string() }),
]);

export type ChatEvent = z.infer<typeof ChatEventSchema>;
```

### Persona types (`src/types/persona.ts`)

```tsx
import { z } from "zod";

export const PersonaSchema = z.object({
  projectType: z.string().nullable(),
  budgetTier: z.string().nullable(),
  role: z.string().nullable(),
  stylePreferences: z.array(z.string()),
  materialPreferences: z.array(z.string()),
  categories: z.array(z.string()),
  rejections: z.array(z.string()),
  approvals: z.array(z.string()),
});

export type Persona = z.infer<typeof PersonaSchema>;

export const FeedbackSignalSchema = z.enum(["like", "dislike"]);

export type FeedbackSignal = z.infer<typeof FeedbackSignalSchema>;

export const EMPTY_PERSONA: Persona = {
  projectType: null,
  budgetTier: null,
  role: null,
  stylePreferences: [],
  materialPreferences: [],
  categories: [],
  rejections: [],
  approvals: [],
};
```

### Product types with Zod (`src/types/product.ts`)

```tsx
import { z } from "zod";

export const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  subcategory: z.string(),
  tags: z.array(z.string()),
  budgetTier: z.string(),
  imageUrl: z.string().url(),
  description: z.string(),
});

export type Product = z.infer<typeof ProductSchema>;

export const RecommendationSchema = z.object({
  product: ProductSchema,
  score: z.number(),
});

export type Recommendation = z.infer<typeof RecommendationSchema>;
```

---

## Validation

Use **Zod** for runtime validation of data from external boundaries. The `ProductSchema` in `src/types/product.ts` is the reference example.

Pattern: define a Zod schema, then derive the TypeScript type with `z.infer<typeof Schema>`. This keeps the runtime validator and static type in perfect sync.

Validate at the API client boundary (`lib/api.ts`), not inside components:

```tsx
// In lib/api.ts — validate response data
export async function fetchRecommendations(sessionId: string, personaEmbedding?: number[]): Promise<Recommendation[]> {
  const res = await fetch("/api/recommend", { ... });
  const data = await res.json();
  return z.array(RecommendationSchema).parse(data);
}
```

---

## Common Patterns

### Discriminated unions for event types

`ChatEvent` in `src/types/chat.ts:14-18` uses a discriminated union on the `type` field. This enables exhaustive switch matching and narrows the type inside each branch.

```tsx
export const ChatEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("token"), content: z.string() }),
  z.object({ type: z.literal("persona_update"), persona: PersonaSchema }),
  z.object({ type: z.literal("done") }),
  z.object({ type: z.literal("error"), message: z.string() }),
]);
```

### Literal types for constrained values

`FeedbackSignal` in `src/types/persona.ts:16` uses a Zod enum plus inferred literal union, not a plain `string`:
```tsx
export const FeedbackSignalSchema = z.enum(["like", "dislike"]);
export type FeedbackSignal = z.infer<typeof FeedbackSignalSchema>;
```

This is used in component props (`ProductCard.tsx:7`):
```tsx
onFeedback: (productId: string, signal: "like" | "dislike") => void;
```

### Constant objects for initial state

`EMPTY_PERSONA` in `src/types/persona.ts:14-23` provides a typed default value. Used in `usePersona.ts:18`:
```tsx
const [persona, setPersona] = useState<Persona>(EMPTY_PERSONA);
```

### Extending native HTML element attributes

`Button.tsx:6-8` extends `ButtonHTMLAttributes` for pass-through props:
```tsx
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}
```

Because `Button` extends native attributes, it should also normalize button semantics in the primitive itself:

```tsx
export function Button({ type, ...props }: ButtonProps) {
  return <button type={type ?? "button"} {...props} />;
}
```

### Import type

Use `import type` for type-only imports. This is enforced by convention throughout the codebase:
```tsx
import type { Message } from "@/types/chat";
import type { Product } from "@/types/product";
import type { Persona, FeedbackSignal } from "@/types/persona";
```

### Stable IDs for streamed message lists

`Message` includes a stable `id` string so streamed assistant content can update the last bubble without using array indices as React keys:

```tsx
function createMessage(role: Message["role"], content: string): Message {
  return {
    id: crypto.randomUUID(),
    role,
    content,
  };
}
```

---

## Forbidden Patterns

| Pattern | Why | Instead |
|---------|-----|---------|
| `any` | Defeats type checking | `unknown` + type guard, or proper type |
| `as` type assertions (except `as const`) | Bypasses type safety | Narrow with type guards |
| `// @ts-ignore` / `// @ts-expect-error` without explanation | Hides real issues | Fix the type error |
| `!` non-null assertion | Runtime null crashes | Handle the null case |
| `enum` | Tree-shaking issues, surprising behavior | `as const` objects or union types (see `FeedbackSignal`) |

---

## Reference Files

| Pattern | File |
|---------|------|
| Zod schema + z.infer | `src/types/product.ts` |
| Discriminated union | `src/types/chat.ts` (ChatEvent) |
| Literal type alias | `src/types/persona.ts` (FeedbackSignal) |
| Typed constant | `src/types/persona.ts` (EMPTY_PERSONA) |
| Extend HTML attributes | `src/components/ui/Button.tsx` (ButtonProps) |
| Hook return interface | `src/hooks/useChat.ts` (UseChatReturn) |
| API client signatures | `src/lib/api.ts` |
