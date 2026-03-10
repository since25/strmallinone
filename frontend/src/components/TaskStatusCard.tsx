import { Card, Descriptions, Tag } from 'antd';
import type { StepStatus, TaskDetail, TaskStatus } from '../types';

const statusColor: Record<TaskStatus | StepStatus, string> = {
  pending: 'default',
  running: 'processing',
  success: 'success',
  failed: 'error',
};

interface TaskStatusCardProps {
  task: TaskDetail | null;
}

export function TaskStatusCard({ task }: TaskStatusCardProps) {
  return (
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
  );
}
