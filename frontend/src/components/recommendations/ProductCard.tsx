"use client";

import Image from "next/image";
import type { FeedbackSignal } from "@/types/persona";
import type { Product } from "@/types/product";
import { Button } from "@/components/ui/Button";

interface ProductCardProps {
  product: Product;
  score: number;
  onFeedback: (
    productId: string,
    signal: FeedbackSignal,
  ) => Promise<void> | void;
  disabled: boolean;
}

export function ProductCard({
  product,
  score,
  onFeedback,
  disabled,
}: ProductCardProps) {
  return (
    <div className="overflow-hidden rounded-[28px] border border-[color:var(--line)] bg-[color:var(--panel)] shadow-[0_24px_60px_rgba(29,42,34,0.08)]">
      <div className="relative aspect-[4/3] bg-[color:var(--accent-soft)]">
        <Image
          src={product.imageUrl}
          alt={product.name}
          fill
          sizes="(max-width: 1536px) 100vw, 50vw"
          unoptimized
          className="object-cover"
        />
        <div className="absolute inset-x-0 top-0 flex items-center justify-between p-4">
          <span className="rounded-full bg-[color:var(--panel)]/85 px-3 py-1 text-[11px] tracking-[0.16em] text-[color:var(--muted)] uppercase shadow-sm backdrop-blur-sm">
            {product.category}
          </span>
          <span className="rounded-full bg-[color:var(--ink)] px-3 py-1 text-[11px] tracking-[0.16em] text-white uppercase">
            {Math.round(score * 100)}% match
          </span>
        </div>
      </div>
      <div className="p-5">
        <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
          {product.subcategory}
        </p>
        <h3 className="mt-2 text-2xl text-[color:var(--ink)]">
          {product.name}
        </h3>
        <p className="mt-3 line-clamp-3 text-sm leading-6 text-[color:var(--muted)]">
          {product.description}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {product.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-[color:var(--line)] bg-white/80 px-3 py-1 text-xs text-[color:var(--muted)]"
            >
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              void onFeedback(product.id, "like");
            }}
            disabled={disabled}
            className="rounded-[18px] px-4 py-3 text-sm"
          >
            More like this
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              void onFeedback(product.id, "dislike");
            }}
            disabled={disabled}
            className="rounded-[18px] px-4 py-3 text-sm"
          >
            Not for me
          </Button>
        </div>
      </div>
    </div>
  );
}
