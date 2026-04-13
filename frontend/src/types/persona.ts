import { z } from "zod";

export const PersonaSchema = z.object({
  projectType: z.string().nullable(),
  budgetTier: z.string().nullable(),
  role: z.string().nullable(),
  stylePreferences: z.array(z.string()),
  materialPreferences: z.array(z.string()),
  categories: z.array(z.string()),
  rejections: z.array(z.string()),
  approvals: z.array(z.string()),
});

export type Persona = z.infer<typeof PersonaSchema>;

export const FeedbackSignalSchema = z.enum(["like", "dislike"]);

export type FeedbackSignal = z.infer<typeof FeedbackSignalSchema>;

export const EMPTY_PERSONA: Persona = {
  projectType: null,
  budgetTier: null,
  role: null,
  stylePreferences: [],
  materialPreferences: [],
  categories: [],
  rejections: [],
  approvals: [],
};
