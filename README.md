# strmallinone

基于 CloudSaver + PanSou 聚合搜索、CloudSaver 115 转存、STRM webhook 生成的前后端一体化 MVP。

任务流程固定为：`search -> transfer -> strm`

## 技术栈

- Frontend: React + Vite + TypeScript + Ant Design
- Backend: Express + TypeScript
- Database: SQLite
- Log streaming: SSE

## 功能概览

- 前端输入关键词并搜索资源
- 后端通过 `CloudSaver adapter` + `PanSou adapter` 聚合搜索资源
- 前端展示统一 DTO 的资源列表
- 用户单选一条资源后提交转存任务
- 后端通过 `CloudSaver 115 adapter` 转存到 115
- 转存成功后调用 `strmwebhook adapter`
- 前端通过 SSE 实时显示任务日志和状态
- SQLite 持久化任务、日志和搜索历史

## 项目结构

```text
strmallinone/
├── backend/
│   ├── src/
│   │   ├── adapters/
│   │   │   ├── cloudsaver/
│   │   │   │   ├── cloudsaver.client.ts
│   │   │   │   ├── cloudsaver.mapper.ts
│   │   │   │   ├── cloudsaver.search.ts
│   │   │   │   ├── cloudsaver.transfer115.ts
│   │   │   │   └── cloudsaver.types.ts
│   │   │   ├── pansou/
│   │   │   │   ├── pansou.client.ts
│   │   │   │   ├── pansou.mapper.ts
│   │   │   │   ├── pansou.search.ts
│   │   │   │   └── pansou.types.ts
│   │   │   └── strmwebhook/
│   │   │       ├── strmwebhook.client.ts
│   │   │       └── strmwebhook.types.ts
│   │   ├── config/
│   │   ├── controllers/
│   │   ├── db/
│   │   ├── repositories/
│   │   ├── routes/
│   │   ├── services/
│   │   └── types/
│   ├── .env.example
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── main.tsx
│   │   └── styles.css
│   └── package.json
├── docs/
│   └── development-guide.md
├── strm_webhook/
├── package.json
└── README.md
```

## 架构说明

### 后端分层

- `controllers`: 只做参数校验和 HTTP 响应，不直接调用第三方接口
- `services`: 编排业务流程
- `adapters`: 封装 CloudSaver 与 strmwebhook 的第三方对接
- `repositories`: SQLite 持久化
- `task-log-stream.service.ts`: SSE 订阅与广播

### 核心服务

- `SearchService`: 聚合 CloudSaver + PanSou 搜索结果，去重后写入 `search_history`
- `TaskService`: 创建任务并异步触发工作流
- `TransferWorkflowService`: 串行执行 `transfer -> strm`
- `TaskLogService`: 统一写日志并推送 SSE

## 环境变量

复制 [backend/.env.example](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/.env.example) 为 `backend/.env`。

当前项目已接入你提供的局域网 CloudSaver 服务。

真实接口需要这些变量：

```env
CLOUDSAVER_BASE_URL=http://192.168.70.120:8008
CLOUDSAVER_SEARCH_PATH=/api/search
CLOUDSAVER_LOGIN_PATH=/api/user/login
CLOUDSAVER_115_SHARE_INFO_PATH=/api/cloud115/share-info
CLOUDSAVER_115_FOLDERS_PATH=/api/cloud115/folders
CLOUDSAVER_115_SAVE_PATH=/api/cloud115/save
CLOUDSAVER_USERNAME=
CLOUDSAVER_PASSWORD=
CLOUDSAVER_AUTH_TOKEN=
CLOUDSAVER_COOKIE=
CLOUDSAVER_USER_AGENT=
CLOUDSAVER_ORIGIN=http://192.168.70.120:8008
CLOUDSAVER_DEFAULT_MOVIE_FOLDER=automv
CLOUDSAVER_DEFAULT_TV_FOLDER=autotv
CLOUDSAVER_MOCK=false
PANSOU_BASE_URL=http://192.168.70.120:8888
PANSOU_SEARCH_PATH=/api/search
PANSOU_ENABLED=true
STRM_WEBHOOK_URL=http://localhost:9527/webhook/strm
STRM_WEBHOOK_MOCK=true
STRM_ALIST_BASE_PATH=/115
```

说明：

- `backend/.env` 已按 `docs/cloudsaver.md` 提供的 curl 填入真实 CloudSaver 地址和鉴权信息
- 如果提供 `CLOUDSAVER_USERNAME` / `CLOUDSAVER_PASSWORD`，后端会自动调用 `POST /api/user/login` 获取 Bearer token
- 自动登录模式下，请求遇到 `401` 会自动重新登录并重试一次
- `PANSOU_ENABLED=true` 时会把 `PanSou` 的 `115` 搜索结果合并到当前搜索列表
- `STRM_WEBHOOK_URL` 已切到 `http://192.168.70.120:9527/webhook/strm`
- 搜索仍然只展示 `pan115/115` 资源，转存与 STRM 仍然只走 CloudSaver 链路

## 安装与启动

```bash
npm install
```

终端 1：

```bash
npm run dev:backend
```

终端 2：

```bash
npm run dev:frontend
```

默认地址：

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:3000](http://localhost:3000)

## Docker 部署

已提供：

- [docker-compose.yml](/Users/wangyichuan/Desktop/wangcode/strmallinone/docker-compose.yml)
- [backend/Dockerfile](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/Dockerfile)
- [frontend/Dockerfile](/Users/wangyichuan/Desktop/wangcode/strmallinone/frontend/Dockerfile)
- [frontend/nginx.conf](/Users/wangyichuan/Desktop/wangcode/strmallinone/frontend/nginx.conf)

启动：

```bash
docker compose up -d --build
```

访问：

- Frontend: [http://localhost:8080](http://localhost:8080)
- Backend: [http://localhost:3000](http://localhost:3000)

说明：

- 前端容器使用 `nginx` 托管静态文件，并反代 `/api` 到 `backend:3000`
- 后端容器直接运行编译产物 `dist/index.js`
- SQLite 数据通过卷挂载到宿主机目录 `./backend/data`
- 容器启动时会读取 `./backend/.env`

停止：

```bash
docker compose down
```

## 构建

```bash
npm run build
```

## API

### `POST /api/search`

请求：

```json
{
  "keyword": "流浪地球",
  "driver": "115",
  "mediaType": "movie"
}
```

### `POST /api/tasks/transfer`

请求：

```json
{
  "keyword": "流浪地球",
  "resource": {
    "id": "res_001",
    "title": "流浪地球 4K",
    "provider": "115",
    "rawType": "video",
    "size": "12GB",
    "shareUrl": "https://...",
    "extra": {}
  }
}
```

### `GET /api/tasks/:taskId`

返回任务状态：

- `status`: `pending | running | success | failed`
- `transferStatus`: `pending | success | failed`
- `strmStatus`: `pending | success | failed`

### `GET /api/tasks/:taskId/logs`

返回该任务的历史日志。

### `GET /api/tasks/:taskId/logs/stream`

SSE 日志流，事件：

- `snapshot`: 当前已有日志
- `ready`: 连接成功
- `log`: 增量日志
- `ping`: 心跳

## SQLite 表

- `transfer_tasks`
- `task_logs`
- `search_history`

数据库默认写到 `backend/data/app.db`。

## 真实接口替换点

### CloudSaver 搜索

实现文件：[backend/src/adapters/cloudsaver/cloudsaver.search.ts](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/src/adapters/cloudsaver/cloudsaver.search.ts)

- 当前支持 mock 搜索结果
- 关闭 `CLOUDSAVER_MOCK` 后会调用真实搜索接口
- 原始响应统一经 `cloudsaver.mapper.ts` 转为前端 DTO
- 已适配真实返回结构：频道分组 `data[] -> list[]`
- 只提取 `cloudType=pan115` 的资源，并解析 `shareCode` / `receiveCode`

### PanSou 搜索聚合

实现文件：[backend/src/adapters/pansou/pansou.search.ts](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/src/adapters/pansou/pansou.search.ts)

- `PANSOU_ENABLED=true` 时调用 `GET /api/search?keyword=...`
- 当前按官方方式调用 `POST /api/search`
- 请求体使用 `kw`，并附带 `cloud_types: ["115"]`
- 只读取 PanSou 返回里的 `merged_by_type['115']`
- 映射为统一 DTO 后与 CloudSaver 结果按 `shareCode + receiveCode` 去重
- 转存不走 PanSou，PanSou 只负责补充搜索结果
- PanSou 来源可能包含已失效分享，真实能否转存仍以 CloudSaver `share-info` 校验结果为准
- PanSou 返回 `data` 为空或接口异常时，会自动降级为只使用 CloudSaver 搜索结果

### CloudSaver 115 转存

实现文件：[backend/src/adapters/cloudsaver/cloudsaver.transfer115.ts](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/src/adapters/cloudsaver/cloudsaver.transfer115.ts)

- 当前支持 mock 转存结果
- 关闭 `CLOUDSAVER_MOCK` 后调用真实 115 转存接口
- 真实链路为：`share-info -> folders -> save`
- 已支持自动选择 `automv` / `autotv`
- 已处理 CloudSaver 的重复转存返回：`文件已接收，无需重复接收`

### STRM webhook

实现文件：[backend/src/adapters/strmwebhook/strmwebhook.client.ts](/Users/wangyichuan/Desktop/wangcode/strmallinone/backend/src/adapters/strmwebhook/strmwebhook.client.ts)

- 当前支持 mock 结果
- 关闭 `STRM_WEBHOOK_MOCK` 后会调用真实 `POST /webhook/strm`
- 请求体默认是：

```json
{
  "path": "/115/资源目录"
}
```

## 已完成约束

- CloudSaver 已封装成 adapter
- controller 未直接调用第三方接口
- 工作流固定为 `search -> transfer -> strm`
- 提供完整项目结构
- 提供 README

## 自测结果

已本地验证：

- `npm run build --workspace backend`
- `npm run build --workspace frontend`
- `POST /api/search`
- `POST /api/tasks/transfer`
- `GET /api/tasks/:taskId`
- `GET /api/tasks/:taskId/logs`
- 真实 CloudSaver 搜索
- 真实 CloudSaver 115 转存
- 真实 STRM webhook

当前未自动化验证浏览器端 SSE 视觉表现，但后端到真实 CloudSaver 与真实 STRM webhook 的链路已跑通。
