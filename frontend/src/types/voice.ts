import { z } from "zod";
import { PersonaSchema } from "./persona";
import { RecommendationSchema } from "./product";

export const VoiceTokenResponseSchema = z.object({
  token: z.string(),
  model: z.string(),
});

export type VoiceTokenResponse = z.infer<typeof VoiceTokenResponseSchema>;

export const TranscriptMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});

export type TranscriptMessage = z.infer<typeof TranscriptMessageSchema>;

export const TranscriptResponseSchema = z.object({
  sessionId: z.string(),
  persona: PersonaSchema.nullable().default(null),
  recommendations: z.array(RecommendationSchema).default([]),
});

export type TranscriptResponse = z.infer<typeof TranscriptResponseSchema>;
