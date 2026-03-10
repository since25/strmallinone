import type { Response } from 'express';

export class TaskLogStreamService {
  private readonly subscribers = new Map<string, Set<Response>>();

  subscribe(taskId: string, res: Response): void {
    const group = this.subscribers.get(taskId) ?? new Set<Response>();
    group.add(res);
    this.subscribers.set(taskId, group);
  }

  unsubscribe(taskId: string, res: Response): void {
    const group = this.subscribers.get(taskId);
    if (!group) {
      return;
    }

    group.delete(res);
    if (group.size === 0) {
      this.subscribers.delete(taskId);
    }
  }

  publish(taskId: string, log: unknown): void {
    const group = this.subscribers.get(taskId);
    if (!group) {
      return;
    }

    const payload = `event: log\ndata: ${JSON.stringify(log)}\n\n`;
    group.forEach((res) => res.write(payload));
  }

  publishSnapshot(taskId: string, logs: unknown[], res: Response): void {
    res.write(`event: snapshot\ndata: ${JSON.stringify(logs)}\n\n`);
    res.write(`event: ready\ndata: ${JSON.stringify({ taskId })}\n\n`);
  }
}
