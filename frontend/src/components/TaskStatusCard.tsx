import { Card, Descriptions, Progress, Tag } from 'antd';
import type { BatchDetail, BatchStatus, StepStatus, TaskDetail, TaskStatus } from '../types';

const statusColor: Record<TaskStatus | StepStatus | BatchStatus, string> = {
  pending: 'default',
  running: 'processing',
  success: 'success',
  partial: 'warning',
  failed: 'error',
};

const statusLabel: Record<TaskStatus | StepStatus | BatchStatus, string> = {
  pending: '等待中',
  running: '处理中',
  success: '已完成',
  partial: '部分完成',
  failed: '失败',
};

interface TaskStatusCardProps {
  task: TaskDetail | null;
  batch?: BatchDetail | null;
}

export function TaskStatusCard({ task, batch }: TaskStatusCardProps) {
  const completedBatchItems = batch ? batch.successCount + batch.skippedCount + batch.failedCount : 0;
  const progress = batch?.totalCount ? Math.round((completedBatchItems / batch.totalCount) * 100) : 0;

  return (
    <>
      <Card title="任务状态" className="panel-card">
        <Descriptions column={1} size="small">
          <Descriptions.Item label="任务 ID">{task?.id ?? '暂无任务'}</Descriptions.Item>
          <Descriptions.Item label="总状态">
            <Tag color={statusColor[task?.status ?? 'pending']}>{task ? statusLabel[task.status] : '暂无任务'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="转存状态">
            <Tag color={statusColor[task?.transferStatus ?? 'pending']}>{task ? statusLabel[task.transferStatus] : '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="STRM 状态">
            <Tag color={statusColor[task?.strmStatus ?? 'pending']}>{task ? statusLabel[task.strmStatus] : '-'}</Tag>
          </Descriptions.Item>
          {task?.errorMessage && <Descriptions.Item label="错误信息">{task.errorMessage}</Descriptions.Item>}
        </Descriptions>
      </Card>
      {batch && (
        <Card title="批次进度" className="panel-card batch-card">
          <Progress percent={progress} status={batch.status === 'failed' ? 'exception' : batch.status === 'success' ? 'success' : 'active'} />
          <Descriptions column={1} size="small">
            <Descriptions.Item label="批次 ID">{batch.id}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusColor[batch.status]}>{statusLabel[batch.status]}</Tag></Descriptions.Item>
            <Descriptions.Item label="总数">{batch.totalCount}</Descriptions.Item>
            <Descriptions.Item label="处理中">{batch.runningCount}</Descriptions.Item>
            <Descriptions.Item label="成功 / 跳过 / 失败">{batch.successCount} / {batch.skippedCount} / {batch.failedCount}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </>
  );
}
