import cors from 'cors';
import express from 'express';
import { env } from './config/env';
import './db/database';
import { CloudSaverClient } from './adapters/cloudsaver/cloudsaver.client';
import { CloudSaverSearchService } from './adapters/cloudsaver/cloudsaver.search';
import { CloudSaverTransfer115Service } from './adapters/cloudsaver/cloudsaver.transfer115';
import { PanSouClient } from './adapters/pansou/pansou.client';
import { PanSouSearchService } from './adapters/pansou/pansou.search';
import { StrmWebhookClient } from './adapters/strmwebhook/strmwebhook.client';
import { SearchController } from './controllers/search.controller';
import { TaskController } from './controllers/task.controller';
import { SearchHistoryRepository } from './repositories/search-history.repository';
import { TaskLogRepository } from './repositories/task-log.repository';
import { TaskRepository } from './repositories/task.repository';
import { createRouter } from './routes';
import { SearchService } from './services/search.service';
import { TaskLogService } from './services/task-log.service';
import { TaskLogStreamService } from './services/task-log-stream.service';
import { TaskService } from './services/task.service';
import { TransferWorkflowService } from './services/transfer-workflow.service';

const app = express();
app.use(cors({ origin: env.FRONTEND_ORIGIN }));
app.use(express.json());

const cloudSaverClient = new CloudSaverClient();
const panSouClient = new PanSouClient();
const searchHistoryRepository = new SearchHistoryRepository();
const taskRepository = new TaskRepository();
const taskLogRepository = new TaskLogRepository();
const taskLogStreamService = new TaskLogStreamService();
const taskLogService = new TaskLogService(taskLogRepository, taskLogStreamService);
const searchService = new SearchService(
  new CloudSaverSearchService(cloudSaverClient),
  new PanSouSearchService(panSouClient),
  searchHistoryRepository,
);
const transferWorkflowService = new TransferWorkflowService(
  taskRepository,
  taskLogService,
  new CloudSaverTransfer115Service(cloudSaverClient),
  new StrmWebhookClient(),
);
const taskService = new TaskService(taskRepository, taskLogService, transferWorkflowService);
const searchController = new SearchController(searchService);
const taskController = new TaskController(taskService, taskLogStreamService);

app.use('/api', createRouter(searchController, taskController));

app.listen(env.PORT, () => {
  console.log(`Backend server listening on http://localhost:${env.PORT}`);
});
