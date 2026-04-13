"use client";

import { useState } from "react";
import type { Recommendation } from "@/types/product";

interface UseRecommendationsReturn {
  products: Recommendation[];
  isLoading: boolean;
  error: string | null;
}

export function useRecommendations(
  _sessionId: string,
): UseRecommendationsReturn {
  const [products] = useState<Recommendation[]>([]);
  const [isLoading] = useState(false);
  const [error] = useState<string | null>(null);

  // TODO: Fetch recommendations from backend when persona has >= 2 signals

  return { products, isLoading, error };
}
