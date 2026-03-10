import { db } from '../db/database';
import type { StepStatus, TaskStatus, TransferTaskDto, TransferTaskRecord } from '../types/task';
import type { ResourceDto } from '../types/resource';

const insertStmt = db.prepare(`
  INSERT INTO transfer_tasks (
    id, keyword, provider, resource_title, resource_payload, status,
    transfer_status, strm_status, error_message, created_at, updated_at
  ) VALUES (
    @id, @keyword, @provider, @resourceTitle, @resourcePayload, @status,
    @transferStatus, @strmStatus, @errorMessage, @createdAt, @updatedAt
  )
`);

const findByIdStmt = db.prepare('SELECT * FROM transfer_tasks WHERE id = ?');
const updateStatusStmt = db.prepare(`
  UPDATE transfer_tasks
  SET status = @status,
      transfer_status = @transferStatus,
      strm_status = @strmStatus,
      error_message = @errorMessage,
      updated_at = @updatedAt
  WHERE id = @id
`);

function mapTask(row: TransferTaskRecord | undefined): TransferTaskDto | null {
  if (!row) {
    return null;
  }

  return {
    id: row.id,
    keyword: row.keyword,
    provider: row.provider,
    resourceTitle: row.resource_title,
    resource: JSON.parse(row.resource_payload) as ResourceDto,
    status: row.status,
    transferStatus: row.transfer_status,
    strmStatus: row.strm_status,
    errorMessage: row.error_message,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export class TaskRepository {
  create(input: { id: string; keyword: string; provider: string; resourceTitle: string; resource: ResourceDto }): void {
    const now = new Date().toISOString();
    insertStmt.run({
      id: input.id,
      keyword: input.keyword,
      provider: input.provider,
      resourceTitle: input.resourceTitle,
      resourcePayload: JSON.stringify(input.resource),
      status: 'pending',
      transferStatus: 'pending',
      strmStatus: 'pending',
      errorMessage: null,
      createdAt: now,
      updatedAt: now,
    });
  }

  findById(id: string): TransferTaskDto | null {
    const row = findByIdStmt.get(id) as TransferTaskRecord | undefined;
    return mapTask(row);
  }

  updateStatuses(input: {
    id: string;
    status: TaskStatus;
    transferStatus: StepStatus;
    strmStatus: StepStatus;
    errorMessage?: string | null;
  }): void {
    updateStatusStmt.run({
      ...input,
      errorMessage: input.errorMessage ?? null,
      updatedAt: new Date().toISOString(),
    });
  }
}
