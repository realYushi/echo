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
