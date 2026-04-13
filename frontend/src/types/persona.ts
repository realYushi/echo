export interface Persona {
  projectType: string | null;
  budgetTier: string | null;
  role: string | null;
  stylePreferences: string[];
  materialPreferences: string[];
  categories: string[];
  rejections: string[];
  approvals: string[];
}

export type FeedbackSignal = "like" | "dislike";

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
