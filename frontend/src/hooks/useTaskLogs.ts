import { useEffect, useRef, useState } from 'react';
import type { TaskLogItem } from '../types';

export function useTaskLogs(taskId: string | null) {
  const [logs, setLogs] = useState<TaskLogItem[]>([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    setLogs([]);
    setConnected(false);

    if (!taskId) {
      return;
    }

    const eventSource = new EventSource(`/api/tasks/${taskId}/logs/stream`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('snapshot', (event) => {
      const snapshot = JSON.parse((event as MessageEvent).data) as TaskLogItem[];
      setLogs(snapshot);
    });

    eventSource.addEventListener('ready', () => {
      setConnected(true);
    });

    eventSource.addEventListener('log', (event) => {
      const item = JSON.parse((event as MessageEvent).data) as TaskLogItem;
      setLogs((current) => {
        if (current.some((entry) => entry.id === item.id)) {
          return current;
        }
        return [...current, item];
      });
    });

    eventSource.onerror = () => {
      setConnected(false);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [taskId]);

  return { logs, connected };
}
