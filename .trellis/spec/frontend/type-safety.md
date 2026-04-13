# Type Safety

> Type safety patterns in this project.

---

## Overview

TypeScript strict mode. No `any` types. Shared types in `src/types/`. Zod for runtime validation of API responses.

---

## Type Organization

- **`src/types/`**: Domain types shared across components and hooks. One file per domain.
- **Component-local types**: `interface {Component}Props` in the component file.
- **API response types**: Defined in `src/types/`, validated with Zod at the API boundary.

```
src/types/
├── chat.ts       # Message, ChatRequest, ChatResponse
├── persona.ts    # Persona, PersonaSignal
└── product.ts    # Product, Recommendation, FeedbackSignal
```

Types should mirror the backend Pydantic schemas. Keep them in sync manually for MVP; share via codegen if drift becomes a problem.

---

## Validation

Use **Zod** for runtime validation of data from external boundaries:

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
```

Validate at the API client boundary (`lib/api.ts`), not inside components:

```tsx
export async function fetchRecommendations(personaEmbedding: number[]): Promise<Product[]> {
  const res = await fetch("/api/recommend", { ... });
  const data = await res.json();
  return z.array(ProductSchema).parse(data.products);
}
```

---

## Common Patterns

- **Discriminated unions** for message types:

```tsx
type ChatEvent =
  | { type: "token"; content: string }
  | { type: "persona_update"; persona: Persona }
  | { type: "done" }
  | { type: "error"; message: string };
```

- **Literal types** for feedback signals: `"like" | "dislike"` (not `string`)
- **`satisfies`** for type-checked object literals without widening

---

## Forbidden Patterns

| Pattern | Why | Instead |
|---------|-----|---------|
| `any` | Defeats type checking | `unknown` + type guard, or proper type |
| `as` type assertions (except `as const`) | Bypasses type safety | Narrow with type guards |
| `// @ts-ignore` / `// @ts-expect-error` without explanation | Hides real issues | Fix the type error |
| `!` non-null assertion | Runtime null crashes | Handle the null case |
| `enum` | Tree-shaking issues, surprising behavior | `as const` objects or union types |
