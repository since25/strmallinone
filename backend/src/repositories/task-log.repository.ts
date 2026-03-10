import { db } from '../db/database';
import type { LogLevel, TaskLogRecord } from '../types/task';

const insertStmt = db.prepare(`
  INSERT INTO task_logs (task_id, level, message, detail, created_at)
  VALUES (@taskId, @level, @message, @detail, @createdAt)
`);
const listByTaskStmt = db.prepare('SELECT * FROM task_logs WHERE task_id = ? ORDER BY id ASC');

export class TaskLogRepository {
  create(input: { taskId: string; level: LogLevel; message: string; detail?: string | null }): TaskLogRecord {
    const createdAt = new Date().toISOString();
    const result = insertStmt.run({
      taskId: input.taskId,
      level: input.level,
      message: input.message,
      detail: input.detail ?? null,
      createdAt,
    });

    return {
      id: Number(result.lastInsertRowid),
      task_id: input.taskId,
      level: input.level,
      message: input.message,
      detail: input.detail ?? null,
      created_at: createdAt,
    };
  }

  listByTask(taskId: string): TaskLogRecord[] {
    return listByTaskStmt.all(taskId) as TaskLogRecord[];
  }
}
