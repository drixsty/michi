import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_ENABLE_ASSISTANT_BETA: z
    .string()
    .optional()
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_ASSISTANT_API_URL: z
    .string()
    .url()
    .default('http://localhost:8001/graphql'),
  NEXT_PUBLIC_MAIN_API_URL: z
    .string()
    .url()
    .default('http://localhost:8000/graphql'),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_ENABLE_ASSISTANT_BETA: process.env.NEXT_PUBLIC_ENABLE_ASSISTANT_BETA,
  NEXT_PUBLIC_ASSISTANT_API_URL: process.env.NEXT_PUBLIC_ASSISTANT_API_URL,
  NEXT_PUBLIC_MAIN_API_URL: process.env.NEXT_PUBLIC_MAIN_API_URL,
});
