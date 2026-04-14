import { z } from "zod";
import { PersonaSchema, type Persona } from "./persona";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  sessionId: string;
  message: string;
  persona: Persona | null;
}

export const ChatEventSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("token"),
    content: z.string(),
  }),
  z.object({
    type: z.literal("suggestions"),
    suggestions: z.array(z.string()),
  }),
  z.object({
    type: z.literal("persona_update"),
    persona: PersonaSchema,
  }),
  z.object({
    type: z.literal("done"),
  }),
  z.object({
    type: z.literal("error"),
    message: z.string(),
  }),
]);

export type ChatEvent = z.infer<typeof ChatEventSchema>;
