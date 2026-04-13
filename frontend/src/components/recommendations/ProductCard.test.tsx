import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ProductCard } from "@/components/recommendations/ProductCard";

describe("ProductCard", () => {
  it("sends like and dislike signals for the active product", () => {
    const onFeedback = vi.fn();

    render(
      <ProductCard
        product={{
          id: "lighting-001",
          name: "Cascading Crystal Chandelier",
          category: "lighting",
          subcategory: "chandelier",
          tags: ["luxury", "crystal", "lighting"],
          budgetTier: "premium",
          imageUrl: "https://example.com/light.png",
          description: "A dramatic lighting piece.",
        }}
        score={0.88}
        onFeedback={onFeedback}
        disabled={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "More like this" }));
    fireEvent.click(screen.getByRole("button", { name: "Not for me" }));

    expect(onFeedback).toHaveBeenNthCalledWith(1, "lighting-001", "like");
    expect(onFeedback).toHaveBeenNthCalledWith(2, "lighting-001", "dislike");
  });
});
