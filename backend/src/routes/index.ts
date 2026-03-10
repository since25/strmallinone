import { Router } from 'express';
import { SearchController } from '../controllers/search.controller';
import { TaskController } from '../controllers/task.controller';

export function createRouter(searchController: SearchController, taskController: TaskController): Router {
  const router = Router();

  router.get('/health', (_req, res) => {
    res.json({ success: true, data: { status: 'ok' } });
  });

  router.post('/search', searchController.search);
  router.post('/tasks/transfer', taskController.createTransferTask);
  router.get('/tasks/:taskId', taskController.getTask);
  router.get('/tasks/:taskId/logs', taskController.getLogs);
  router.get('/tasks/:taskId/logs/stream', taskController.streamLogs);

  return router;
}
