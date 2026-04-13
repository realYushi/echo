import { z } from "zod";

export const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  subcategory: z.string(),
  tags: z.array(z.string()),
  budgetTier: z.string(),
  imageUrl: z.string().url(),
  description: z.string(),
});

export type Product = z.infer<typeof ProductSchema>;

export const RecommendationSchema = z.object({
  product: ProductSchema,
  score: z.number(),
});

export type Recommendation = z.infer<typeof RecommendationSchema>;
