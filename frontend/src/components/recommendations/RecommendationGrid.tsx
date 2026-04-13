"use client";

import type { Recommendation } from "@/types/product";
import { ProductCard } from "@/components/recommendations/ProductCard";
import { EmptyState } from "@/components/recommendations/EmptyState";

interface RecommendationGridProps {
  products: Recommendation[];
  onFeedback: (productId: string, signal: "like" | "dislike") => void;
  isLoading: boolean;
}

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
