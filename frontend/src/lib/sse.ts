import { postChat } from "@/lib/api";
import { createLogger } from "@/lib/logger";
import {
  ChatEventSchema,
  type ChatEvent,
  type ChatRequest,
} from "@/types/chat";

const logger = createLogger("sse");

function parseChunk(chunk: string): ChatEvent | null {
  const payload = chunk
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .join("");

  if (!payload) {
    return null;
  }

  try {
    return ChatEventSchema.parse(JSON.parse(payload));
  } catch (err) {
    logger.error({ err, payload: payload.slice(0, 200) }, "sse_parse_error");
    return null;
  }
}

export async function streamChat(
  request: ChatRequest,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const stream = await postChat(request, signal);
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        const event = parseChunk(chunk);
        if (event) {
          onEvent(event);
        }
      }

      if (done) {
        if (buffer.trim()) {
          const event = parseChunk(buffer);
          if (event) {
            onEvent(event);
          }
        }
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
