import type { ChatEvent } from "@/types/chat";

class NotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not yet implemented`);
    this.name = "NotImplementedError";
  }
}

export async function streamChat(
  _sessionId: string,
  _message: string,
  _onEvent: (event: ChatEvent) => void,
): Promise<void> {
  throw new NotImplementedError("streamChat");
}
