# 项目开发指南：基于 CloudSaver + 115 转存 + STRM Webhook 的前后端应用

## 1. 项目目标

开发一个带前端界面的 Web 应用，完成以下完整链路：
- 用户在前端输入关键词
- 前端调用后端搜索接口
- 后端通过 CloudSaver 抓包得到的私有接口执行资源检索
- 前端展示搜索结果
- 用户单选一条资源
- 前端提交“转存任务”
- 后端调用 CloudSaver 的 115 转存接口
- 转存成功后，后端继续调用 strmwebhook
- 前端实时看到任务日志
- 最终显示完整结果：搜索成功 / 转存成功 / STRM 生成成功

## 2. 开发原则

### 2.1 总体原则

这个项目要按 **分层架构** 来写，不要把抓包参数、CloudSaver 调用逻辑、115 转存逻辑、STRM webhook 调用逻辑全部揉在一个文件里。

必须拆成：
- 前端层
- 后端 API 层
- 第三方接口适配层
- 任务编排层
- 日志与任务状态层

这样后续你增加 夸克 / 阿里云盘 / 其他驱动 时，不需要重写整个项目。

### 2.2 MVP 范围

第一版只做：
- CloudSaver 搜索
- 115 驱动展示
- 单选一条结果
- 调用 115 转存
- 调用 strmwebhook
- 页面日志展示
- 基础错误处理

第一版不要先做太多高级功能，比如：
- 多选批量转存
- 用户系统
- 权限系统
- 多任务队列调度
- 高级筛选
- 多平台驱动联动
- 定时任务

这些等 MVP 跑通后再迭代。

## 3. 技术选型建议

### 3.1 推荐技术栈

#### 前端
- React
- Vite
- TypeScript
- Ant Design 或者 shadcn/ui 二选一
- axios
- Zustand 或 React Query

#### 后端
- Node.js
- TypeScript
- NestJS 或 Express

#### 推荐方案（Codex 优先）
如果让 Codex 开发，我更建议：
- **前端**：React + Vite + TypeScript + Ant Design
- **后端**：Express + TypeScript
- **数据库**：SQLite（MVP）
- **日志**：文件日志 + 数据库存储
- **实时输出**：SSE 优先，WebSocket 次选

**原因**：
- Express 更轻，Codex 更容易快速落地
- SQLite 足够做任务记录
- SSE 非常适合任务日志流式展示

## 4. 系统架构

### 4.1 整体架构图（逻辑）

```text
[Browser 前端]
    |
    | HTTP / SSE
    v
[Backend API Server]
    |
    |-- SearchService
    |     └── CloudSaverAdapter
    |
    |-- TransferWorkflowService
    |     ├── CloudSaver115Adapter
    |     ├── StrmWebhookAdapter
    |     └── TaskLogService
    |
    |-- Database
          ├── search_history
          ├── transfer_tasks
          └── task_logs
```

### 4.2 模块拆分

#### 前端模块
- 搜索页
- 搜索结果列表
- 单选操作区
- 任务执行按钮
- 日志面板
- 历史任务页（可选）

#### 后端模块
- 搜索接口模块
- 转存任务模块
- CloudSaver 适配模块
- strmwebhook 适配模块
- 日志模块
- 配置模块

## 5. 功能拆解

### 5.1 搜索功能

#### 用户行为
用户在前端输入关键词，点击搜索。

#### 系统行为
- **前端请求**：`POST /api/search`
  ```json
  {
    "keyword": "流浪地球",
    "driver": "115"
  }
  ```
- **后端处理**：
  1. 校验参数
  2. 调用 `CloudSaverAdapter.search(keyword, driver)`
  3. 将结果标准化
  4. 返回给前端

#### 返回结果统一格式
不管 CloudSaver 原始返回格式是什么，后端都要转换为统一结构：
```json
{
  "success": true,
  "data": [
    {
      "id": "res_001",
      "title": "流浪地球2 4K",
      "provider": "115",
      "rawType": "video",
      "size": "12.4GB",
      "shareUrl": "xxx",
      "extra": {
        "source": "cloudsaver",
        "raw": {}
      }
    }
  ]
}
```

#### 关键要求
- 后端不要把抓包原始字段直接暴露给前端
- 要做一层 DTO 转换
- 前端只依赖统一字段，不依赖 CloudSaver 私有字段名

### 5.2 搜索结果展示

前端展示表格字段建议：
- 单选框
- 标题
- 类型
- 大小
- 来源驱动
- 分享链接 / 资源标识
- 操作状态

> 第一版默认只支持 115，但前端字段要预留 `provider`。

### 5.3 单选并执行转存

用户在前端选中一条记录后，点击：**“转存并生成 STRM”**

- **前端请求**：`POST /api/tasks/transfer`
  ```json
  {
    "resourceId": "res_001",
    "resourcePayload": {
      "title": "流浪地球2 4K",
      "provider": "115",
      "shareUrl": "xxx",
      "extra": {}
    }
  }
  ```

#### 后端工作流
1. 创建任务记录 `transfer_tasks`
2. 写入日志：开始处理
3. 调用 CloudSaver 115 转存接口
4. 写入日志：转存成功 / 失败
5. 如果转存成功，调用 strmwebhook
6. 写入日志：STRM 成功 / 失败
7. 更新任务最终状态
8. 前端通过 SSE 看到全过程

### 5.4 日志展示

日志要支持前端实时看到，不要等整个流程结束才返回。

- **推荐方案**：SSE
- **后端提供**：`GET /api/tasks/:taskId/logs/stream`
- **前端使用**：`EventSource` 订阅。

#### 日志结构
```json
{
  "taskId": "task_xxx",
  "level": "info",
  "message": "开始调用 115 转存接口",
  "timestamp": "2026-03-10T12:00:00Z"
}
```

#### 日志级别建议
- `info`
- `success`
- `warning`
- `error`

> 前端可以用 different colors 显示。

## 6. CloudSaver 接口适配设计

### 6.1 核心原则

CloudSaver API 不公开，所以必须做成独立适配层，不要散落在业务逻辑里。

**目录示例**：
```text
backend/src/adapters/cloudsaver/
  ├── cloudsaver.client.ts
  ├── cloudsaver.search.ts
  ├── cloudsaver.transfer115.ts
  ├── cloudsaver.types.ts
  └── cloudsaver.mapper.ts
```

### 6.2 适配器职责

- **cloudsaver.client.ts**：负责基础请求封装、Cookie / Token / Header 注入、超时、重试、错误统一处理。
- **cloudsaver.search.ts**：负责搜索接口调用，返回原始结果。
- **cloudsaver.transfer115.ts**：负责调用 115 转存接口，返回转存结果。
- **cloudsaver.mapper.ts**：负责原始响应转统一 DTO。

### 6.3 不要硬编码的内容

抓包得到的以下内容，不要写死在业务代码里，应统一放在配置文件或环境变量里：
- Base URL
- Authorization
- Cookie
- 特殊请求头（user-agent, referer, app-id, csrf token 等）
- driver id
- endpoint path

**例如 (.env)**：
```env
CLOUDSAVER_BASE_URL=
CLOUDSAVER_COOKIE=
CLOUDSAVER_AUTH_TOKEN=
CLOUDSAVER_SEARCH_PATH=
CLOUDSAVER_TRANSFER_115_PATH=
CLOUDSAVER_USER_AGENT=
```

### 6.4 抓包接口接入方式

Codex 开发时，不需要真实抓包复原逻辑写死在代码里，而是按下面方式实现：
1. **先做一个“接口占位版本”**：要求 Codex 先实现一个 adapter，支持 `search` 和 `transferTo115` 方法。
2. **内部用 mock 数据** 或你后续补充的真实抓包字段实现。

这样可以分步走：
1. 第一阶段先把系统流程打通
2. 第二阶段你把真实抓包接口字段替换进去

## 7. strmwebhook 集成设计

### 7.1 已知条件
你已经有：
- strmwebhook 的调用地址
- strmwebhook 的源码

所以这里必须把 strmwebhook 作为一个下游服务对接，而不是把逻辑写死在本项目里。

### 7.2 调用方式

建议封装：
```text
backend/src/adapters/strmwebhook/
  ├── strmwebhook.client.ts
  ├── strmwebhook.types.ts
  └── strmwebhook.mapper.ts
```

定义统一调用：
```typescript
generateStrm(input: {
  taskId: string;
  transferResult: any;
  resource: any;
}): Promise<StrmWebhookResult>
```

### 7.3 webhook 调用结果

统一返回结构：
```json
{
  "success": true,
  "message": "STRM 生成成功",
  "data": {
    "path": "/media/电影/流浪地球2",
    "count": 1
  }
}
```

## 8. 数据库设计

MVP 推荐 SQLite。

### 8.1 表：transfer_tasks
```sql
CREATE TABLE transfer_tasks (
  id TEXT PRIMARY KEY,
  keyword TEXT,
  provider TEXT,
  resource_title TEXT,
  resource_payload TEXT,
  status TEXT,
  transfer_status TEXT,
  strm_status TEXT,
  error_message TEXT,
  created_at TEXT,
  updated_at TEXT
);
```

#### 状态建议
- **总状态 status**：`pending`, `running`, `success`, `failed`
- **转存状态 transfer_status**：`pending`, `success`, `failed`
- **strm 状态 strm_status**：`pending`, `success`, `failed`

### 8.2 表：task_logs
```sql
CREATE TABLE task_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT,
  level TEXT,
  message TEXT,
  detail TEXT,
  created_at TEXT
);
```

### 8.3 表：search_history (可选)
```sql
CREATE TABLE search_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword TEXT,
  driver TEXT,
  result_count INTEGER,
  created_at TEXT
);
```

## 9. 前端页面设计

### 9.1 主页面布局
建议单页完成 MVP：
- **区块一：搜索区**：输入框（关键词）、驱动选择（默认 115）、搜索按钮。
- **区块二：结果区**：表格展示搜索结果，支持单选。
- **区块三：操作区**：转存并生成 STRM 按钮、当前任务状态标签。
- **区块四：日志区**：实时滚动日志，支持清空显示和按级别高亮。

### 9.2 页面交互要求
- **搜索中**：按钮 loading，禁止重复点击。
- **搜索完成**：自动展示结果表格，默认不选中任何条目。
- **执行任务中**：锁定当前结果，按钮变成 loading，开启 SSE 订阅日志。
- **任务完成**：显示 success / failed，解锁按钮，保留日志。

## 10. 后端接口设计

### 10.1 搜索接口
- **POST** `/api/search`
- **请求体**：
  ```json
  { "keyword": "xxx", "driver": "115" }
  ```
- **响应体**：见 5.1

### 10.2 创建转存任务
- **POST** `/api/tasks/transfer`
- **请求体**：
  ```json
  {
    "keyword": "流浪地球",
    "resource": {
      "id": "res_001",
      "title": "xxx",
      "provider": "115",
      "shareUrl": "xxx",
      "extra": {}
    }
  }
  ```
- **响应体**：
  ```json
  { "success": true, "data": { "taskId": "task_123" } }
  ```

### 10.3 查询任务详情
- **GET** `/api/tasks/:taskId`
- **响应体**：
  ```json
  {
    "success": true,
    "data": {
      "id": "task_123",
      "status": "running",
      "transferStatus": "success",
      "strmStatus": "pending"
    }
  }
  ```

### 10.4 查询任务日志
- **GET** `/api/tasks/:taskId/logs`

### 10.5 实时日志流
- **GET** `/api/tasks/:taskId/logs/stream` (使用 SSE)

## 11. 任务编排逻辑

核心服务建议命名：`TransferWorkflowService`

**伪代码**：
```typescript
async run(taskId: string, input: TransferInput) {
  log(taskId, 'info', '任务开始');
  try {
    updateTaskStatus(taskId, 'running');
    log(taskId, 'info', '开始调用 CloudSaver 115 转存');
    const transferResult = await cloudSaver115Adapter.transfer(input.resource);
    if (!transferResult.success) {
      log(taskId, 'error', '115 转存失败');
      updateTaskFail(taskId, 'transfer failed');
      return;
    }
    log(taskId, 'success', '115 转存成功');

    log(taskId, 'info', '开始调用 strmwebhook');
    const strmResult = await strmWebhookAdapter.generateStrm({
      taskId,
      transferResult,
      resource: input.resource,
    });
    if (!strmResult.success) {
      log(taskId, 'error', 'STRM 生成失败');
      updateTaskFail(taskId, 'strm failed');
      return;
    }
    log(taskId, 'success', 'STRM 生成成功');
    updateTaskSuccess(taskId);
  } catch (error) {
    log(taskId, 'error', `任务异常: ${error.message}`);
    updateTaskFail(taskId, error.message);
  }
}
```

## 12. 错误处理设计

必须区分这几类错误：

### 12.1 搜索阶段错误
- CloudSaver 未登录 / cookie 失效
- 搜索参数无效
- 接口变更
- 返回为空

### 12.2 转存阶段错误
- 115 转存失败
- 链接失效
- 重复转存
- 权限不足
- CloudSaver 接口异常

### 12.3 STRM 阶段错误
- strmwebhook 地址不可达
- 参数格式不匹配
- 生成失败
- 下游服务返回 500

### 12.4 系统错误
- 数据库写入失败
- SSE 中断
- JSON 解析失败
- 超时

## 13. 日志规范

日志必须结构化，每条日志至少包含：
```json
{
  "taskId": "task_123",
  "stage": "transfer",
  "level": "info",
  "message": "开始调用 115 转存接口",
  "detail": "",
  "timestamp": "2026-03-10T12:00:00.000Z"
}
```

**stage 建议值**：`search`, `transfer`, `strm`, `system`

## 14. 配置管理

必须有 `.env` 文件，禁止把密钥写进代码仓库。

**建议配置项**：
```env
PORT=3000
NODE_ENV=development
DB_PATH=./data/app.db
CLOUDSAVER_BASE_URL=
CLOUDSAVER_COOKIE=
CLOUDSAVER_AUTH_TOKEN=
CLOUDSAVER_SEARCH_PATH=
CLOUDSAVER_TRANSFER_115_PATH=
CLOUDSAVER_USER_AGENT=
STRM_WEBHOOK_URL=
STRM_WEBHOOK_TOKEN=
LOG_LEVEL=info
REQUEST_TIMEOUT=15000
```

## 15. 目录结构建议

```text
project-root/
  ├── frontend/
  │   ├── src/
  │   │   ├── api/
  │   │   ├── components/
  │   │   ├── pages/
  │   │   ├── hooks/
  │   │   ├── store/
  │   │   ├── types/
  │   │   └── App.tsx
  │   ├── package.json
  │   └── vite.config.ts
  │
  ├── backend/
  │   ├── src/
  │   │   ├── adapters/
  │   │   │   ├── cloudsaver/
  │   │   │   └── strmwebhook/
  │   │   ├── controllers/
  │   │   ├── services/
  │   │   ├── repositories/
  │   │   ├── models/
  │   │   ├── routes/
  │   │   ├── utils/
  │   │   ├── config/
  │   │   └── app.ts
  │   ├── data/
  │   ├── package.json
  │   └── tsconfig.json
  │
  ├── docs/
  │   ├── api.md
  │   ├── architecture.md
  │   └── development-plan.md
  │
  ├── .env.example
  ├── docker-compose.yml
  └── README.md
```

## 16. 开发阶段拆分

### 第一阶段：搭骨架
- **目标**：前后端项目初始化，基础页面可打开，后端 API 可运行，SQLite 接入，日志表建好。
- **交付标准**：前端能输入关键词，后端返回 mock 搜索结果，页面展示 mock 表格，能创建 mock 任务并实时显示 mock 日志。

### 第二阶段：接入真实搜索
- **目标**：接入 CloudSaver 搜索接口，完成搜索结果标准化。
- **交付标准**：输入真实关键词可以拿到真实搜索结果，前端表格正常展示。

### 第三阶段：接入 115 转存
- **目标**：接入 CloudSaver 的 115 转存能力，任务流跑通到转存完成。
- **交付标准**：选中资源后可执行真实转存，日志能显示调用过程，数据库记录任务状态。

### 第四阶段：接入 strmwebhook
- **目标**：转存完成后继续调用 strmwebhook。
- **交付标准**：整个链路跑通，最终状态 success，页面日志完整。

### 第五阶段：增强健壮性
- **目标**：重试、参数校验、错误提示、任务详情页、搜索历史等。

## 17. 对 Codex 的具体开发要求

### 给 Codex 的开发指令

请按以下要求从零开始实现一个前后端分离项目：

#### 项目目标
实现一个 Web 应用，支持：
1. 输入关键词搜索资源
2. 后端通过 CloudSaver 私有接口执行搜索
3. 前端展示结果，当前默认只支持 115 驱动
4. 用户单选一个资源
5. 提交后触发后端任务：
   - 先调用 CloudSaver 的 115 转存接口
   - 再调用 strmwebhook
6. 前端实时展示任务日志
7. 最终显示任务成功或失败

#### 技术要求
- monorepo 结构
- frontend: React + Vite + TypeScript + Ant Design
- backend: Express + TypeScript
- database: SQLite
- real-time log: SSE
- 使用 dotenv 管理配置
- 必须拆分 adapter 层，不允许把 CloudSaver 请求直接写进 controller

#### 架构要求
后端至少包含：`SearchController`, `TaskController`, `CloudSaverAdapter`, `StrmWebhookAdapter`, `TransferWorkflowService`, `TaskLogService`, SQLite repository 层.

#### 数据要求
至少创建 `transfer_tasks` 和 `task_logs` 表。

#### API 要求
实现：`POST /api/search`, `POST /api/tasks/transfer`, `GET /api/tasks/:taskId`, `GET /api/tasks/:taskId/logs`, `GET /api/tasks/:taskId/logs/stream`。

#### 开发步骤
1. 先完成可运行的 mock 版本。
2. 所有第三方接口先抽象成 adapter，并提供 mock 和 real 的切换能力。
3. 提供 `.env.example`, `README`, 基本错误处理和格式良好的目录结构。

#### 注意事项
- 不要把第三方接口原始字段直接传给前端，所有响应都要经过 mapper 标准化。
- 不要先做用户系统或复杂权限，先做 MVP 可运行版本。
- 代码包含基础注释，输出前后端启动命令。

## 18. 推荐的迭代方向

MVP 跑通后，再做下面这些：

### 18.1 多驱动支持
将 provider 扩展成：115, 夸克, 阿里云盘，并将结果按驱动聚合。

### 18.2 搜索历史与任务历史
支持查看过去的搜索关键词、成功任务、失败任务。

### 18.3 批量任务
支持多选资源批量转存。

### 18.4 去重校验
同一个资源重复转存前先检查是否已处理。

### 18.5 高级筛选
按文件大小、类型、来源、时间进行筛选。

## 19. 风险提示

这个项目的最大不确定性不在前端，而在 **CloudSaver 私有接口稳定性**。一定要在设计上保证：
- 接口字段、Header、Cookie、请求体构造、响应映射等均可配置且独立。
- 一旦接口变化，只改 adapter，不动业务层。

## 20. 最终交付物要求

要求至少交付以下内容：
- 可运行的前后端项目
- SQLite 初始化脚本
- `.env.example` 和 README
- mock 适配器和 real adapter 接口占位文件
- 基础 UI 和 SSE 日志流
- 一个完整可演示的任务链路
