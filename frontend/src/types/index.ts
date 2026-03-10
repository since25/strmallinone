export type Provider = '115';
export type MediaType = 'movie' | 'tv';
export type LogLevel = 'info' | 'success' | 'warning' | 'error';
export type TaskStatus = 'pending' | 'running' | 'success' | 'failed';
export type StepStatus = 'pending' | 'success' | 'failed';

export interface ResourceItem {
  id: string;
  title: string;
  provider: Provider;
  mediaType: MediaType;
  rawType: string;
  size: string;
  shareUrl: string;
  extra: Record<string, unknown>;
}

export interface TaskLogItem {
  id: number;
  taskId: string;
  level: LogLevel;
  message: string;
  detail: string | null;
  createdAt: string;
}

export interface TaskDetail {
  id: string;
  keyword: string;
  provider: string;
  resourceTitle: string;
  resource: ResourceItem;
  status: TaskStatus;
  transferStatus: StepStatus;
  strmStatus: StepStatus;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
