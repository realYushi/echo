import { z } from "zod";
import { PersonaSchema } from "@/types/persona";
import { RecommendationSchema } from "@/types/product";

export const SessionHistoryMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});

export type SessionHistoryMessage = z.infer<typeof SessionHistoryMessageSchema>;

export const SessionSnapshotSchema = z.object({
  sessionId: z.string(),
  messages: z.array(SessionHistoryMessageSchema),
  persona: PersonaSchema.nullable(),
  recommendations: z.array(RecommendationSchema),
});

export type SessionSnapshot = z.infer<typeof SessionSnapshotSchema>;
