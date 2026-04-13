import { z } from "zod";
import type { ChatRequest } from "@/types/chat";
import {
  PersonaSchema,
  type FeedbackSignal,
  type Persona,
} from "@/types/persona";
import { RecommendationSchema, type Recommendation } from "@/types/product";

const ApiErrorSchema = z.object({
  error: z.object({
    message: z.string(),
  }),
});

const FeedbackResponseSchema = z.object({
  persona: PersonaSchema,
});

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    const parsed = ApiErrorSchema.safeParse(data);
    if (parsed.success) {
      return parsed.data.error.message;
    }
  } catch {
    // Ignore JSON parsing errors and fall back to the status text.
  }

  return response.statusText || `Request failed with status ${response.status}`;
}

export async function postChat(
  request: ChatRequest,
  signal?: AbortSignal,
): Promise<ReadableStream<Uint8Array>> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  if (!response.body) {
    throw new Error("Chat stream is unavailable.");
  }

  return response.body;
}

export async function postFeedback(
  productId: string,
  signal: FeedbackSignal,
  sessionId: string,
): Promise<{ persona: Persona }> {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ productId, signal, sessionId }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  const data = await response.json();
  return FeedbackResponseSchema.parse(data);
}

export async function fetchRecommendations(
  sessionId: string,
  personaEmbedding?: number[],
  signal?: AbortSignal,
): Promise<Recommendation[]> {
  const payload: { sessionId: string; personaEmbedding?: number[] } = {
    sessionId,
  };
  if (personaEmbedding && personaEmbedding.length > 0) {
    payload.personaEmbedding = personaEmbedding;
  }

  const response = await fetch("/api/recommend", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  const data = await response.json();
  return z.array(RecommendationSchema).parse(data);
}
