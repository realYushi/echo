"use client";

import { useCallback, useEffect, useState } from "react";
import { postFeedback } from "@/lib/api";
import type { Persona, FeedbackSignal } from "@/types/persona";
import { EMPTY_PERSONA } from "@/types/persona";

interface UsePersonaReturn {
  persona: Persona;
  setPersona: (persona: Persona) => void;
  sendFeedback: (
    productId: string,
    signal: FeedbackSignal,
  ) => Promise<Persona | null>;
  isSubmitting: boolean;
  error: string | null;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to update your taste profile right now.";
}

export function usePersona(sessionId: string): UsePersonaReturn {
  const [persona, setPersonaState] = useState<Persona>(EMPTY_PERSONA);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPersonaState(EMPTY_PERSONA);
    setIsSubmitting(false);
    setError(null);
  }, [sessionId]);

  const setPersona = useCallback((nextPersona: Persona) => {
    setError(null);
    setPersonaState(nextPersona);
  }, []);

  const sendFeedback = useCallback(
    async (productId: string, signal: FeedbackSignal) => {
      if (!sessionId) {
        return null;
      }

      setIsSubmitting(true);
      setError(null);

      try {
        const response = await postFeedback(productId, signal, sessionId);
        setPersonaState(response.persona);
        return response.persona;
      } catch (nextError) {
        setError(getErrorMessage(nextError));
        return null;
      } finally {
        setIsSubmitting(false);
      }
    },
    [sessionId],
  );

  return { persona, setPersona, sendFeedback, isSubmitting, error };
}
