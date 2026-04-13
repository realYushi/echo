# Component Guidelines

> How components are built in this project.

---

## Overview

React functional components with TypeScript. Tailwind CSS for styling. No class components. Named exports only (`export function`, never `export default` for components).

Page components (`app/*/page.tsx`) are the sole exception -- they use `export default function` as required by Next.js App Router.

---

## Component Structure

Standard order within a component file:

1. `"use client"` directive (if the component uses hooks, event handlers, or browser APIs)
2. Imports (React, types, sibling components, lib utilities)
3. Props interface named `{Component}Props`
4. Exported component function
5. Hooks first, then handlers, then return JSX

**Actual example** from `src/components/recommendations/ProductCard.tsx`:

```tsx
"use client";

import type { Product } from "@/types/product";
import { Button } from "@/components/ui/Button";

interface ProductCardProps {
  product: Product;
  onFeedback: (productId: string, signal: "like" | "dislike") => void;
}

export function ProductCard({ product, onFeedback }: ProductCardProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <div className="aspect-[4/3] bg-gray-100">
        <img
          src={product.imageUrl}
          alt={product.name}
          className="h-full w-full object-cover"
        />
      </div>
      <div className="p-4">
        <h3 className="font-medium">{product.name}</h3>
        <p className="mt-1 text-sm text-gray-500">{product.category}</p>
        <p className="mt-2 text-sm text-gray-600 line-clamp-2">{product.description}</p>
        <div className="mt-3 flex gap-2">
          <Button variant="ghost" onClick={() => onFeedback(product.id, "like")}>
            More like this
          </Button>
          <Button variant="ghost" onClick={() => onFeedback(product.id, "dislike")}>
            Not for me
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

## Props Conventions

- Define props as an `interface` named `{Component}Props` in the same file
- Destructure props in the function signature
- Use `children: React.ReactNode` for composition, not custom render props
- Event handlers: `on{Event}` naming (`onFeedback`, `onSend`)

**Actual examples**:

`src/components/chat/ChatPanelProps` (`ChatPanel.tsx:7-11`):
```tsx
interface ChatPanelProps {
  messages: Message[];
  onSend: (message: string) => void;
  isStreaming: boolean;
}
```

`src/components/chat/ChatInput.tsx:6-9`:
```tsx
interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}
```

`src/components/recommendations/RecommendationGrid.tsx:7-11`:
```tsx
interface RecommendationGridProps {
  products: Recommendation[];
  onFeedback: (productId: string, signal: "like" | "dislike") => void;
  isLoading: boolean;
}
```

**Anti-pattern** -- avoid inline types in function signatures:
```tsx
// Bad: inline types
function ChatInput({ onSend, disabled }: { onSend: (m: string) => void; disabled?: boolean }) { ... }
```

---

## Variant Pattern (UI Primitives)

The Button component demonstrates the variant pattern used for UI primitives.

**From** `src/components/ui/Button.tsx`:

```tsx
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({ variant = "primary", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-lg px-4 py-2 font-medium transition-colors disabled:opacity-50",
        variant === "primary" && "bg-gray-900 text-white hover:bg-gray-800",
        variant === "secondary" && "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50",
        variant === "ghost" && "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

Key patterns:
- Extend `ButtonHTMLAttributes` so all native button props pass through
- Variant as string union with default value
- Accept optional `className` for consumer overrides
- Spread `...props` to forward native attributes
- `cn()` merges base, variant, and override classes without conflicts

---

## Styling Patterns

- **Tailwind CSS** for all styling
- Use `cn()` helper (from `clsx` + `tailwind-merge`) for conditional classes -- see `src/lib/utils.ts`
- No CSS modules or styled-components
- Responsive: desktop-first (the discovery UI is desktop-only for MVP)

**Conditional class example** from `src/components/chat/MessageBubble.tsx:11-17`:
```tsx
<div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
  <div
    className={cn(
      "max-w-[80%] rounded-2xl px-4 py-3",
      isUser ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-900",
    )}
  >
```

---

## Loading, Empty, and Error States

Components that display async data must handle three states: loading, empty, and populated.

**From** `src/components/recommendations/RecommendationGrid.tsx`:

```tsx
export function RecommendationGrid({ products, onFeedback, isLoading }: RecommendationGridProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-400">Loading recommendations...</p>
      </div>
    );
  }

  if (products.length === 0) {
    return <EmptyState />;
  }

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold">Recommendations</h2>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {products.map((rec) => (
          <ProductCard key={rec.product.id} product={rec.product} onFeedback={onFeedback} />
        ))}
      </div>
    </div>
  );
}
```

`src/components/recommendations/EmptyState.tsx` is a dedicated component for the no-results state.

---

## Accessibility

- Interactive elements must be `<button>` or `<a>`, not `<div onClick>`
- Images require `alt` text (see `ProductCard.tsx:18`)
- Form inputs require associated labels or descriptive placeholders (see `ChatInput.tsx:30`)
- Focus management for the chat input after message send
- `ChatInput` uses a `<form>` with `onSubmit` so Enter key works natively (`ChatInput.tsx:14`)

---

## Common Mistakes

- **Don't put business logic in components** -- extract to hooks or `lib/`
- **Don't use `useEffect` for derived state** -- compute during render
- **Don't create wrapper components that just pass props through** -- compose directly
- **Don't forget `"use client"` directive** -- required for any component using hooks, state, or event handlers (all chat/ and recommendation/ components need it)
- **Don't use `export default`** for components -- use named exports. Page components are the exception.

---

## Reference Files

| Pattern | File |
|---------|------|
| UI primitive with variants | `src/components/ui/Button.tsx` |
| Feature container with composition | `src/components/chat/ChatPanel.tsx` |
| Conditional styling with cn() | `src/components/chat/MessageBubble.tsx` |
| Form with controlled input | `src/components/chat/ChatInput.tsx` |
| Feedback callback pattern | `src/components/recommendations/ProductCard.tsx` |
| Loading/empty/populated states | `src/components/recommendations/RecommendationGrid.tsx` |
| Empty state component | `src/components/recommendations/EmptyState.tsx` |
