import { Card, Empty, Space, Tag, Typography } from 'antd';
import type { TaskLogItem } from '../types';

const colorMap = {
  info: 'blue',
  success: 'green',
  warning: 'gold',
  error: 'red',
} as const;

interface LogPanelProps {
  logs: TaskLogItem[];
  connected: boolean;
}

export function LogPanel({ logs, connected }: LogPanelProps) {
  return (
    <Card
      title="实时日志"
      extra={<Tag color={connected ? 'green' : 'default'}>{connected ? 'SSE 已连接' : 'SSE 未连接'}</Tag>}
      className="panel-card"
    >
      {logs.length === 0 ? (
        <Empty description="任务日志会在这里实时出现" />
      ) : (
        <div className="log-list">
          {logs.map((log) => (
            <div key={log.id} className="log-item">
              <Space align="start" size={12}>
                <Tag color={colorMap[log.level]}>{log.level}</Tag>
                <div>
                  <Typography.Text>{log.message}</Typography.Text>
                  <Typography.Paragraph type="secondary" className="log-time">
                    {new Date(log.createdAt).toLocaleString()}
                  </Typography.Paragraph>
                </div>
              </Space>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
