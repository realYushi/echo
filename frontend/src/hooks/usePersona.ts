"use client";

import { useState, useCallback } from "react";
import type { Persona, FeedbackSignal } from "@/types/persona";
import { EMPTY_PERSONA } from "@/types/persona";

interface PersonaSignal {
  productId: string;
  signal: FeedbackSignal;
}

interface UsePersonaReturn {
  persona: Persona;
  addSignal: (signal: PersonaSignal) => void;
}

export function usePersona(): UsePersonaReturn {
  const [persona, setPersona] = useState<Persona>(EMPTY_PERSONA);

  const addSignal = useCallback(
    (signal: PersonaSignal) => {
      // TODO: Send feedback to backend and update persona from response
      setPersona((prev) => {
        if (signal.signal === "like") {
          return {
            ...prev,
            approvals: [...prev.approvals, signal.productId],
          };
        }
        return {
          ...prev,
          rejections: [...prev.rejections, signal.productId],
        };
      });
    },
    [],
  );

  return { persona, addSignal };
}
