"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRecommendations } from "@/lib/api";
import type { Recommendation } from "@/types/product";

interface UseRecommendationsReturn {
  products: Recommendation[];
  isLoading: boolean;
  error: string | null;
  refreshRecommendations: () => Promise<Recommendation[]>;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to refresh recommendations right now.";
}

export function useRecommendations(
  sessionId: string,
): UseRecommendationsReturn {
  const [products, setProducts] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const refreshRecommendations = useCallback(async () => {
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    setIsLoading(true);
    setError(null);

    try {
      const nextProducts = await fetchRecommendations(
        sessionId,
        undefined,
        controller.signal,
      );
      setProducts(nextProducts);
      return nextProducts;
    } catch (nextError) {
      if (isAbortError(nextError)) {
        return [];
      }

      setError(getErrorMessage(nextError));
      return [];
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
      setIsLoading(false);
    }
  }, [sessionId]);

  return { products, isLoading, error, refreshRecommendations };
}
