import { z } from "zod";
import type { ChatRequest } from "@/types/chat";
import { createLogger, getRequestId } from "@/lib/logger";
import {
  PersonaSchema,
  type FeedbackSignal,
  type Persona,
} from "@/types/persona";
import { RecommendationSchema, type Recommendation } from "@/types/product";
import { SessionSnapshotSchema, type SessionSnapshot } from "@/types/session";
import {
  VoiceTokenResponseSchema,
  TranscriptResponseSchema,
  type VoiceTokenResponse,
  type TranscriptMessage,
  type TranscriptResponse,
} from "@/types/voice";

const logger = createLogger("api");

const ApiErrorSchema = z.object({
  error: z.object({
    message: z.string(),
  }),
});

const FeedbackResponseSchema = z.object({
  persona: PersonaSchema,
});

function requestHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Request-ID": getRequestId(),
  };
}

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
    headers: requestHeaders(),
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: "/api/chat" }, message);
    throw new Error(message);
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
    headers: requestHeaders(),
    body: JSON.stringify({ productId, signal, sessionId }),
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: "/api/feedback", productId, signal }, message);
    throw new Error(message);
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
    headers: requestHeaders(),
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: "/api/recommend", sessionId }, message);
    throw new Error(message);
  }

  const data = await response.json();
  return z.array(RecommendationSchema).parse(data);
}

export async function fetchSessionSnapshot(
  sessionId: string,
  signal?: AbortSignal,
): Promise<SessionSnapshot> {
  const response = await fetch(`/api/sessions/${sessionId}`, {
    method: "GET",
    headers: { "X-Request-ID": getRequestId() },
    signal,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: `/api/sessions/${sessionId}` }, message);
    throw new Error(message);
  }

  const data = await response.json();
  return SessionSnapshotSchema.parse(data);
}

export async function fetchVoiceToken(
  signal?: AbortSignal,
): Promise<VoiceTokenResponse> {
  const response = await fetch("/api/voice/token", {
    method: "POST",
    headers: { "X-Request-ID": getRequestId() },
    signal,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: "/api/voice/token" }, message);
    throw new Error(message);
  }

  const data = await response.json();
  return VoiceTokenResponseSchema.parse(data);
}

export async function postVoiceTranscript(
  sessionId: string,
  messages: TranscriptMessage[],
  signal?: AbortSignal,
): Promise<TranscriptResponse> {
  const response = await fetch("/api/voice/transcript", {
    method: "POST",
    headers: requestHeaders(),
    body: JSON.stringify({ sessionId, messages }),
    signal,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response);
    logger.error({ status: response.status, path: "/api/voice/transcript", sessionId }, message);
    throw new Error(message);
  }

  const data = await response.json();
  return TranscriptResponseSchema.parse(data);
}
