import type { Request, Response } from 'express';
import { z } from 'zod';
import { TaskService } from '../services/task.service';
import { TaskLogStreamService } from '../services/task-log-stream.service';

const resourceSchema = z.object({
  id: z.string(),
  title: z.string(),
  provider: z.literal('115'),
  mediaType: z.enum(['movie', 'tv']),
  rawType: z.string(),
  size: z.string(),
  shareUrl: z.string(),
  extra: z.record(z.string(), z.unknown()).or(z.record(z.unknown())),
});

const createTaskSchema = z.object({
  keyword: z.string().trim().min(1),
  resource: resourceSchema,
});

export class TaskController {
  constructor(
    private readonly taskService: TaskService,
    private readonly taskLogStreamService: TaskLogStreamService,
  ) {}

  createTransferTask = (req: Request, res: Response): void => {
    const parsed = createTaskSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, error: parsed.error.issues[0]?.message ?? 'invalid payload' });
      return;
    }

    const data = this.taskService.createTransferTask(parsed.data);
    res.status(201).json({ success: true, data });
  };

  getTask = (req: Request, res: Response): void => {
    const taskId = String(req.params.taskId);
    const task = this.taskService.getTask(taskId);
    if (!task) {
      res.status(404).json({ success: false, error: 'task not found' });
      return;
    }

    res.json({ success: true, data: task });
  };

  getLogs = (req: Request, res: Response): void => {
    const taskId = String(req.params.taskId);
    res.json({ success: true, data: this.taskService.getLogs(taskId) });
  };

  streamLogs = (req: Request, res: Response): void => {
    const taskId = String(req.params.taskId);
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders?.();

    const logs = this.taskService.getLogs(taskId);
    this.taskLogStreamService.publishSnapshot(taskId, logs, res);
    this.taskLogStreamService.subscribe(taskId, res);

    const heartbeat = setInterval(() => {
      res.write('event: ping\ndata: {}\n\n');
    }, 15000);

    req.on('close', () => {
      clearInterval(heartbeat);
      this.taskLogStreamService.unsubscribe(taskId, res);
      res.end();
    });
  };
}
