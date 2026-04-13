import type { ChatRequest } from "@/types/chat";
import type { Persona, FeedbackSignal } from "@/types/persona";
import type { Recommendation } from "@/types/product";

class NotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not yet implemented`);
    this.name = "NotImplementedError";
  }
}

export async function postChat(
  _request: ChatRequest,
): Promise<ReadableStream<Uint8Array>> {
  throw new NotImplementedError("postChat");
}

export async function postFeedback(
  _productId: string,
  _signal: FeedbackSignal,
  _sessionId: string,
): Promise<{ persona: Persona }> {
  throw new NotImplementedError("postFeedback");
}

export async function fetchRecommendations(
  _sessionId: string,
  _personaEmbedding: number[],
): Promise<Recommendation[]> {
  throw new NotImplementedError("fetchRecommendations");
}
