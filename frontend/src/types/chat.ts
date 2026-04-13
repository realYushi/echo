import type { Persona } from "./persona";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  sessionId: string;
  message: string;
  persona: Persona | null;
}

export type ChatEvent =
  | { type: "token"; content: string }
  | { type: "persona_update"; persona: Persona }
  | { type: "done" }
  | { type: "error"; message: string };
