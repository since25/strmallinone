import type { ResourceDto } from './resource';

export type TaskStatus = 'pending' | 'running' | 'success' | 'failed';
export type StepStatus = 'pending' | 'success' | 'failed';
export type LogLevel = 'info' | 'success' | 'warning' | 'error';

export interface TransferTaskRecord {
  id: string;
  keyword: string;
  provider: string;
  resource_title: string;
  resource_payload: string;
  status: TaskStatus;
  transfer_status: StepStatus;
  strm_status: StepStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransferTaskDto {
  id: string;
  keyword: string;
  provider: string;
  resourceTitle: string;
  resource: ResourceDto;
  status: TaskStatus;
  transferStatus: StepStatus;
  strmStatus: StepStatus;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TaskLogRecord {
  id: number;
  task_id: string;
  level: LogLevel;
  message: string;
  detail: string | null;
  created_at: string;
}
