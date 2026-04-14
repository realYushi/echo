import { z } from "zod";

export const PersonaSchema = z.object({
  budgetTier: z.string().nullable(),
  likes: z.array(z.string()),
  hates: z.array(z.string()),
  approvals: z.array(z.string()),
  rejections: z.array(z.string()),
});

export type Persona = z.infer<typeof PersonaSchema>;

export const FeedbackSignalSchema = z.enum(["like", "dislike"]);

export type FeedbackSignal = z.infer<typeof FeedbackSignalSchema>;

export const EMPTY_PERSONA: Persona = {
  budgetTier: null,
  likes: [],
  hates: [],
  approvals: [],
  rejections: [],
};
