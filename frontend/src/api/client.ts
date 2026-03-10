import type { ApiResponse, MediaType, ResourceItem, TaskDetail, TaskLogItem } from '../types';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const payload = (await response.json()) as ApiResponse<T>;
  if (!response.ok || !payload.success || payload.data === undefined) {
    throw new Error(payload.error ?? 'Request failed');
  }

  return payload.data;
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

export function getTask(taskId: string): Promise<TaskDetail> {
  return request<TaskDetail>(`/api/tasks/${taskId}`);
}

export function getTaskLogs(taskId: string): Promise<TaskLogItem[]> {
  return request<TaskLogItem[]>(`/api/tasks/${taskId}/logs`);
}
