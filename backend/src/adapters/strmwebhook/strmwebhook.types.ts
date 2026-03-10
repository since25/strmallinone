import type { ResourceDto } from '../../types/resource';
import type { CloudSaverTransferResult } from '../cloudsaver/cloudsaver.types';

export interface GenerateStrmInput {
  taskId: string;
  transferResult: CloudSaverTransferResult;
  resource: ResourceDto;
}

export interface StrmWebhookResult {
  success: boolean;
  message: string;
  data?: {
    path: string;
    count: number;
  };
  raw?: unknown;
}
