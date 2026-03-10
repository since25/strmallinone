import { env } from '../../config/env';
import type { GenerateStrmInput, StrmWebhookResult } from './strmwebhook.types';

interface StrmWebhookRawResponse {
  code?: number;
  message?: string;
  path?: string;
  created_count?: number;
  skipped_count?: number;
  error_count?: number;
  details?: {
    created?: string[];
    skipped?: string[];
    errors?: string[];
  };
}

export class StrmWebhookClient {
  async generateStrm(input: GenerateStrmInput): Promise<StrmWebhookResult> {
    const relativePath = input.transferResult.data?.savePath ?? input.resource.title;
    const savePath = relativePath.startsWith(env.STRM_ALIST_BASE_PATH)
      ? relativePath
      : `${env.STRM_ALIST_BASE_PATH.replace(/\/$/, '')}/${relativePath.replace(/^\//, '')}`;

    if (env.STRM_WEBHOOK_MOCK) {
      return {
        success: true,
        message: 'Mock STRM generated',
        data: {
          path: savePath,
          count: input.transferResult.data?.fileCount ?? 1,
        },
        raw: {
          mocked: true,
        },
      };
    }

    const shareFiles = Array.isArray((input.transferResult.raw as { shareFiles?: unknown } | undefined)?.shareFiles)
      ? ((input.transferResult.raw as { shareFiles?: Array<{ fileName: string; isFolder: boolean }> }).shareFiles ?? [])
      : [];
    const parentPath = savePath.includes('/') ? savePath.slice(0, savePath.lastIndexOf('/')) : env.STRM_ALIST_BASE_PATH;
    const looksLikeFile = /\.[A-Za-z0-9]{2,5}$/.test(savePath);
    const directFiles =
      shareFiles.length > 0 && shareFiles.every((item) => !item.isFolder)
        ? shareFiles.length === 1
          ? [savePath]
          : shareFiles.map((item) => `${parentPath}/${item.fileName}`)
        : looksLikeFile
          ? [savePath]
          : null;
    const url = directFiles ? `${env.STRM_WEBHOOK_URL.replace(/\/$/, '')}/direct` : env.STRM_WEBHOOK_URL;
    const payload = directFiles ? { files: directFiles } : { path: savePath };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(env.STRM_WEBHOOK_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error(`STRM webhook failed with status ${response.status}`);
    }

    const raw = (await response.json()) as StrmWebhookRawResponse;
    const errorCount = raw.error_count ?? 0;
    if (errorCount > 0) {
      return {
        success: false,
        message: raw.details?.errors?.[0] ?? raw.message ?? 'STRM 生成失败',
        data: {
          path: savePath,
          count: raw.created_count ?? 0,
        },
        raw,
      };
    }

    return {
      success: true,
      message: raw.message ?? 'STRM 生成成功',
      data: {
        path: savePath,
        count: (raw.created_count ?? 0) + (raw.skipped_count ?? 0),
      },
      raw,
    };
  }
}
