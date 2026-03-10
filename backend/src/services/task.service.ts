import { nanoid } from 'nanoid';
import type { ResourceDto } from '../types/resource';
import { TaskRepository } from '../repositories/task.repository';
import { TransferWorkflowService } from './transfer-workflow.service';
import { TaskLogService } from './task-log.service';

export class TaskService {
  constructor(
    private readonly taskRepository: TaskRepository,
    private readonly taskLogService: TaskLogService,
    private readonly transferWorkflowService: TransferWorkflowService,
  ) {}

  createTransferTask(input: { keyword: string; resource: ResourceDto }): { taskId: string } {
    const taskId = `task_${nanoid(10)}`;
    this.taskRepository.create({
      id: taskId,
      keyword: input.keyword,
      provider: input.resource.provider,
      resourceTitle: input.resource.title,
      resource: input.resource,
    });
    this.taskLogService.append(taskId, 'info', '任务已创建，等待执行');

    void this.transferWorkflowService.run(taskId, { resource: input.resource });

    return { taskId };
  }

  getTask(taskId: string) {
    return this.taskRepository.findById(taskId);
  }

  getLogs(taskId: string) {
    return this.taskLogService.listByTask(taskId);
  }
}
