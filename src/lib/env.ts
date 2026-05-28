import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  REDIS_URL: z.string().min(1),
  LLM_MODEL: z.string().min(1),
  LLM_THINKING_ENABLED: z.enum(["true", "false"]),
  LLM_API_KEY: z.string().min(1),
  LLM_BASE_URL: z.string().min(1),
  FEISHU_APP_ID: z.string().min(1),
  FEISHU_APP_SECRET: z.string().min(1),
  FEISHU_API_BASE_URL: z.string().min(1),
});

export const env = envSchema.parse({
  DATABASE_URL: process.env.DATABASE_URL,
  REDIS_URL: process.env.REDIS_URL,
  LLM_MODEL: process.env.LLM_MODEL,
  LLM_THINKING_ENABLED: process.env.LLM_THINKING_ENABLED,
  LLM_API_KEY: process.env.LLM_API_KEY,
  LLM_BASE_URL: process.env.LLM_BASE_URL,
  FEISHU_APP_ID: process.env.FEISHU_APP_ID,
  FEISHU_APP_SECRET: process.env.FEISHU_APP_SECRET,
  FEISHU_API_BASE_URL: process.env.FEISHU_API_BASE_URL,
});
