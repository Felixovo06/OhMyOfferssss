import { z } from "zod";

export const questionBankScopeSchema = z.enum(["PERSONAL", "GROUP"]);

export const createQuestionBankSchema = z.object({
  name: z.string().trim().min(2).max(120),
  scope: questionBankScopeSchema,
  groupId: z.string().min(1).optional(),
});

export const updateQuestionBankSchema = createQuestionBankSchema.partial().extend({
  id: z.string().min(1),
});

export const createQuestionSchema = z.object({
  bankId: z.string().min(1),
  question: z.string().trim().min(5).max(2000),
  answer: z.string().trim().min(1).max(5000),
  difficultyScore: z.number().int().min(0).max(100),
  tagNames: z.array(z.string().trim().min(1).max(50)).min(1),
  enabled: z.boolean().optional().default(true),
});

export const updateQuestionSchema = createQuestionSchema.partial().extend({
  id: z.string().min(1),
});

export const questionQuerySchema = z.object({
  bankId: z.string().min(1).optional(),
  groupId: z.string().min(1).optional(),
  tag: z.string().trim().min(1).optional(),
  minDifficulty: z.coerce.number().int().min(0).max(100).optional(),
  maxDifficulty: z.coerce.number().int().min(0).max(100).optional(),
  keyword: z.string().trim().min(1).optional(),
  enabled: z.coerce.boolean().optional(),
});

export type CreateQuestionBankInput = z.infer<typeof createQuestionBankSchema>;
export type UpdateQuestionBankInput = z.infer<typeof updateQuestionBankSchema>;
export type CreateQuestionInput = z.infer<typeof createQuestionSchema>;
export type UpdateQuestionInput = z.infer<typeof updateQuestionSchema>;
export type QuestionQueryInput = z.infer<typeof questionQuerySchema>;
