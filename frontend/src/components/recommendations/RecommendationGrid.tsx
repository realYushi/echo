"use client";

import type { FeedbackSignal } from "@/types/persona";
import type { Recommendation } from "@/types/product";
import { ProductCard } from "@/components/recommendations/ProductCard";
import { EmptyState } from "@/components/recommendations/EmptyState";

interface RecommendationGridProps {
  products: Recommendation[];
  onFeedback: (
    productId: string,
    signal: FeedbackSignal,
  ) => Promise<void> | void;
  isLoading: boolean;
  isFeedbackPending: boolean;
  error: string | null;
  emptyTitle: string;
  emptyDescription: string;
}

export function RecommendationGrid({
  products,
  onFeedback,
  isLoading,
  isFeedbackPending,
  error,
  emptyTitle,
  emptyDescription,
}: RecommendationGridProps) {
  if (isLoading && products.length === 0) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-[28px] border border-[color:var(--line)] bg-white/55">
        <p className="text-sm tracking-[0.18em] text-[color:var(--muted)] uppercase">
          Loading recommendations
        </p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="space-y-4">
        {error ? (
          <div className="rounded-[22px] border border-amber-300/60 bg-amber-50/80 px-4 py-3 text-sm text-amber-900">
            {error}
          </div>
        ) : null}
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
            Live shortlist
          </p>
          <h2 className="mt-2 text-2xl text-[color:var(--ink)]">
            Products moving to the top.
          </h2>
        </div>
        <span className="rounded-full border border-[color:var(--line)] bg-white/80 px-3 py-1 text-xs tracking-[0.16em] text-[color:var(--muted)] uppercase">
          {isLoading ? "Refreshing" : `${products.length} active`}
        </span>
      </div>
      {error ? (
        <div className="mb-4 rounded-[22px] border border-amber-300/60 bg-amber-50/80 px-4 py-3 text-sm text-amber-900">
          {error}
        </div>
      ) : null}
      <div className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
        {products.map((rec) => (
          <ProductCard
            key={rec.product.id}
            product={rec.product}
            score={rec.score}
            onFeedback={onFeedback}
            disabled={isFeedbackPending}
          />
        ))}
      </div>
    </div>
  );
}
