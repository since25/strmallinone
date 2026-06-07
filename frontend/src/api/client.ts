import type { ApiResponse, ManualTransferRequest, MediaType, ResourceItem, TaskDetail, TaskLogItem } from '../types';

type ErrorPayload = Partial<ApiResponse<unknown>> & {
  detail?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function formatValidationDetail(detail: unknown): string | null {
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((item) => {
      if (typeof item === 'string') {
        return item.trim();
      }

      if (!isRecord(item) || typeof item.msg !== 'string') {
        return null;
      }

      const location = Array.isArray(item.loc)
        ? item.loc.filter((part): part is string | number => typeof part === 'string' || typeof part === 'number')
        : [];
      const message = item.msg.trim();

      return location.length > 0 ? `${location.join('.')}: ${message}` : message;
    })
    .filter((message): message is string => Boolean(message));

  return messages.length > 0 ? messages.join('; ') : null;
}

function getErrorMessage(payload: unknown): string {
  if (!isRecord(payload)) {
    return 'Request failed';
  }

  const errorPayload = payload as ErrorPayload;
  if (typeof errorPayload.error === 'string' && errorPayload.error.trim()) {
    return errorPayload.error;
  }

  if (typeof errorPayload.detail === 'string' && errorPayload.detail.trim()) {
    return errorPayload.detail;
  }

  return formatValidationDetail(errorPayload.detail) ?? 'Request failed';
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const payload = await parseJson(response);
  if (!response.ok || !isRecord(payload) || !payload.success || payload.data === undefined) {
    throw new Error(getErrorMessage(payload));
  }

  return payload.data as T;
}

export function searchResources(keyword: string, driver: '115', mediaType: MediaType): Promise<ResourceItem[]> {
  return request<ResourceItem[]>('/api/search', {
    method: 'POST',
    body: JSON.stringify({ keyword, driver, mediaType }),
  });
}

export function createTransferTask(keyword: string, resource: ResourceItem): Promise<{ taskId: string }> {
  return request<{ taskId: string }>('/api/tasks/transfer', {
    method: 'POST',
    body: JSON.stringify({ keyword, resource }),
  });
}

export function createManualTransferTask(payload: ManualTransferRequest): Promise<{ taskId: string }> {
  return request<{ taskId: string }>('/api/tasks/manual-transfer', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getTask(taskId: string): Promise<TaskDetail> {
  return request<TaskDetail>(`/api/tasks/${taskId}`);
}

export function getTaskLogs(taskId: string): Promise<TaskLogItem[]> {
  return request<TaskLogItem[]>(`/api/tasks/${taskId}/logs`);
}
