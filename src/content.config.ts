import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const ingredientItem = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("group_header"),
    group: z.string(),
  }),
  z.object({
    type: z.literal("ingredient"),
    amount: z.coerce.string().default(""),
    unit: z.string().default(""),
    name: z.string(),
    notes: z.string().optional(),
  }),
]);

const instructionItem = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("group_header"),
    group: z.string(),
  }),
  z.object({
    type: z.literal("step"),
    text: z.string(),
  }),
]);

const recipes = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/recipes" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    date: z.coerce.date(),
    description: z.string().default(""),
    category: z.string().default(""),
    tags: z.array(z.string()).default([]),
    prepTime: z.number().default(0),
    cookTime: z.number().default(0),
    totalTime: z.number().default(0),
    servings: z.coerce.string().default(""),
    servingsUnit: z.string().optional(),
    ingredients: z.array(ingredientItem),
    instructions: z.array(instructionItem),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/pages" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
  }),
});

export const collections = { recipes, pages };
