"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRecommendations } from "@/lib/api";
import { createLogger } from "@/lib/logger";
import type { Recommendation } from "@/types/product";

const logger = createLogger("useRecommendations");

interface UseRecommendationsReturn {
  products: Recommendation[];
  setRecommendations: (products: Recommendation[]) => void;
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

  useEffect(() => {
    abortControllerRef.current?.abort();
    setProducts([]);
    setIsLoading(false);
    setError(null);
  }, [sessionId]);

  const setRecommendations = useCallback((nextProducts: Recommendation[]) => {
    setError(null);
    setProducts(nextProducts);
  }, []);

  const refreshRecommendations = useCallback(async () => {
    if (!sessionId) {
      return [];
    }

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

      const message = getErrorMessage(nextError);
      logger.error({ err: nextError, sessionId, event: "recommendations_fetch_failed" }, message);
      setError(message);
      return [];
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
      setIsLoading(false);
    }
  }, [sessionId]);

  return {
    products,
    setRecommendations,
    isLoading,
    error,
    refreshRecommendations,
  };
}
