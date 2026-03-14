import type { ResourceDto } from '../types/resource';
import { CloudSaverTransfer115Service } from '../adapters/cloudsaver/cloudsaver.transfer115';
import { StrmWebhookClient } from '../adapters/strmwebhook/strmwebhook.client';
import { TaskRepository } from '../repositories/task.repository';
import { TaskLogService } from './task-log.service';

export class TransferWorkflowService {
  constructor(
    private readonly taskRepository: TaskRepository,
    private readonly taskLogService: TaskLogService,
    private readonly cloudSaverTransfer115Service: CloudSaverTransfer115Service,
    private readonly strmWebhookClient: StrmWebhookClient,
  ) {}

  async run(taskId: string, input: { resource: ResourceDto }): Promise<void> {
    this.taskRepository.updateStatuses({
      id: taskId,
      status: 'running',
      transferStatus: 'pending',
      strmStatus: 'pending',
    });
    this.taskLogService.append(taskId, 'info', '任务开始');
    this.taskLogService.append(taskId, 'info', '开始调用 CloudSaver 115 转存');

    try {
      const transferResult = await this.cloudSaverTransfer115Service.transfer(input.resource);
      if (!transferResult.success || !transferResult.data) {
        const message = transferResult.message || '115 转存失败';
        this.taskLogService.append(taskId, 'error', message);
        this.taskRepository.updateStatuses({
          id: taskId,
          status: 'failed',
          transferStatus: 'failed',
          strmStatus: 'pending',
          errorMessage: message,
        });
        return;
      }

      this.taskRepository.updateStatuses({
        id: taskId,
        status: 'running',
        transferStatus: 'success',
        strmStatus: 'pending',
      });
      this.taskLogService.append(taskId, 'success', `115 转存成功: ${transferResult.data.savePath}`);
      this.taskLogService.append(
        taskId,
        'info',
        `115 保存名称解析: ${transferResult.data.sourceName} -> ${transferResult.data.savedName}`,
      );
      this.taskLogService.append(taskId, 'info', '开始调用 strmwebhook');

      const strmResult = await this.strmWebhookClient.generateStrm({
        taskId,
        transferResult,
        resource: input.resource,
      });

      if (!strmResult.success) {
        const message = strmResult.message || 'STRM 生成失败';
        this.taskLogService.append(taskId, 'error', message);
        this.taskRepository.updateStatuses({
          id: taskId,
          status: 'failed',
          transferStatus: 'success',
          strmStatus: 'failed',
          errorMessage: message,
        });
        return;
      }

      this.taskRepository.updateStatuses({
        id: taskId,
        status: 'success',
        transferStatus: 'success',
        strmStatus: 'success',
      });
      this.taskLogService.append(taskId, 'success', `STRM 生成成功: ${strmResult.data?.path ?? '-'}`);
      this.taskLogService.append(taskId, 'success', '任务完成');
    } catch (error) {
      const message = error instanceof Error ? error.message : '未知异常';
      this.taskLogService.append(taskId, 'error', `任务异常: ${message}`);
      this.taskRepository.updateStatuses({
        id: taskId,
        status: 'failed',
        transferStatus: 'failed',
        strmStatus: 'failed',
        errorMessage: message,
      });
    }
  }
}
