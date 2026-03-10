import path from 'node:path';
import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const booleanFromEnv = z
  .union([z.boolean(), z.string()])
  .optional()
  .transform((value) => {
    if (typeof value === 'boolean') {
      return value;
    }
    if (value === undefined) {
      return undefined;
    }

    return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
  });

const envSchema = z.object({
  PORT: z.coerce.number().default(3000),
  FRONTEND_ORIGIN: z.string().default('http://localhost:5173'),
  DATABASE_PATH: z.string().default('./data/app.db'),
  CLOUDSAVER_BASE_URL: z.string().default('http://192.168.70.120:8008'),
  CLOUDSAVER_SEARCH_PATH: z.string().default('/api/search'),
  CLOUDSAVER_LOGIN_PATH: z.string().default('/api/user/login'),
  CLOUDSAVER_115_SHARE_INFO_PATH: z.string().default('/api/cloud115/share-info'),
  CLOUDSAVER_115_FOLDERS_PATH: z.string().default('/api/cloud115/folders'),
  CLOUDSAVER_115_SAVE_PATH: z.string().default('/api/cloud115/save'),
  CLOUDSAVER_USERNAME: z.string().optional(),
  CLOUDSAVER_PASSWORD: z.string().optional(),
  CLOUDSAVER_AUTH_TOKEN: z.string().optional(),
  CLOUDSAVER_COOKIE: z.string().optional(),
  CLOUDSAVER_USER_AGENT: z.string().optional(),
  CLOUDSAVER_ORIGIN: z.string().default('http://192.168.70.120:8008'),
  CLOUDSAVER_DEFAULT_MOVIE_FOLDER: z.string().default('automv'),
  CLOUDSAVER_DEFAULT_TV_FOLDER: z.string().default('autotv'),
  CLOUDSAVER_MOCK: booleanFromEnv.default(true),
  PANSOU_BASE_URL: z.string().default('http://192.168.70.120:8888'),
  PANSOU_SEARCH_PATH: z.string().default('/api/search'),
  PANSOU_ENABLED: booleanFromEnv.default(true),
  STRM_WEBHOOK_URL: z.string().default('http://localhost:9527/webhook/strm'),
  STRM_WEBHOOK_TIMEOUT_MS: z.coerce.number().default(30000),
  STRM_WEBHOOK_MOCK: booleanFromEnv.default(true),
  STRM_ALIST_BASE_PATH: z.string().default('/115'),
});

const parsed = envSchema.parse(process.env);

export const env = {
  ...parsed,
  DATABASE_PATH: path.resolve(process.cwd(), parsed.DATABASE_PATH),
};
