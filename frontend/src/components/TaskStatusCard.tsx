import { Card, Descriptions, Progress, Tag } from 'antd';
import type { BatchDetail, StepStatus, TaskDetail, TaskStatus } from '../types';

const statusColor: Record<TaskStatus | StepStatus, string> = {
  pending: 'default',
  running: 'processing',
  success: 'success',
  failed: 'error',
};

interface TaskStatusCardProps {
  task: TaskDetail | null;
  batch?: BatchDetail | null;
}

export function TaskStatusCard({ task, batch }: TaskStatusCardProps) {
  return (
    <>
      <Card title="任务状态" className="panel-card">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="任务 ID">{task?.id ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="总状态">
          <Tag color={statusColor[task?.status ?? 'pending']}>{task?.status ?? '-'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="转存状态">
          <Tag color={statusColor[task?.transferStatus ?? 'pending']}>{task?.transferStatus ?? '-'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="STRM 状态">
          <Tag color={statusColor[task?.strmStatus ?? 'pending']}>{task?.strmStatus ?? '-'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="错误信息">{task?.errorMessage ?? '-'}</Descriptions.Item>
      </Descriptions>
      </Card>
      {batch && (
        <Card title="批次进度" className="panel-card batch-card">
          <Progress
            percent={batch.totalCount ? Math.round(((batch.successCount + batch.skippedCount + batch.failedCount) / batch.totalCount) * 100) : 0}
            status={batch.status === 'failed' ? 'exception' : batch.status === 'success' ? 'success' : 'active'}
          />
          <Descriptions column={1} size="small">
            <Descriptions.Item label="批次 ID">{batch.id}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={batch.status === 'failed' ? 'error' : batch.status === 'success' ? 'success' : 'processing'}>{batch.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="总数">{batch.totalCount}</Descriptions.Item>
            <Descriptions.Item label="运行中">{batch.runningCount}</Descriptions.Item>
            <Descriptions.Item label="成功 / 跳过 / 失败">{batch.successCount} / {batch.skippedCount} / {batch.failedCount}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </>
  );
}
