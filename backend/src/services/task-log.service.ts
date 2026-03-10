import type { LogLevel, TaskLogRecord } from '../types/task';
import { TaskLogRepository } from '../repositories/task-log.repository';
import { TaskLogStreamService } from './task-log-stream.service';

function mapLogRecord(record: TaskLogRecord) {
  return {
    id: record.id,
    taskId: record.task_id,
    level: record.level,
    message: record.message,
    detail: record.detail,
    createdAt: record.created_at,
  };
}

export class TaskLogService {
  constructor(
    private readonly repository: TaskLogRepository,
    private readonly streamService: TaskLogStreamService,
  ) {}

  append(taskId: string, level: LogLevel, message: string, detail?: string) {
    const record = this.repository.create({ taskId, level, message, detail });
    const dto = mapLogRecord(record);
    this.streamService.publish(taskId, dto);
    return dto;
  }

  listByTask(taskId: string) {
    return this.repository.listByTask(taskId).map(mapLogRecord);
  }
}
