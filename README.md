# strmallinone

## 当前迁移状态

当前运行后端是 `FastAPI + PanSou + p115 + AList/STRM` 一体化链路；旧的 `Express + CloudSaver + strm_webhook` 代码仅保留作迁移历史。

当前 Python 后端位于 `backend_py/`：

- 搜索：只调用 PanSou 原生 API，不再聚合 CloudSaver。
- 转存：使用 `P115_COOKIE` 直接调用 p115，CloudSaver 已从转存链路解耦。
- STRM：原 `strm_webhook` 能力已合并进 FastAPI 后端，仍依赖 AList `/d` URL 供 Emby 播放。
- Docker：`docker-compose.yml` 的 backend 服务已切换到 `backend_py/Dockerfile`，端口仍为 `3000`，前端可保持原 API 调用方式。
- 批量转存：搜索结果按 `provider + shareCode + receiveCode` 去重，前端支持多选并创建批次；批次使用默认 2、上限 4 的有界并发。
- 幂等：单任务和批次子任务按资源键加目标目录复用活动/成功任务，失败任务可重试。

`shareCode` 是 115 分享链接 `/s/...` 里的分享 ID，`receiveCode` 是提取码/访问码。后端会优先从完整 `shareUrl` 自动解析，正常情况下你不需要手动拆。

新的部署和环境变量说明见 [docs/fastapi-backend.md](/Users/wangyichuan/Desktop/wangcodemac/strmallinone/docs/fastapi-backend.md)。

旧版 TypeScript 后端目录和 CloudSaver 文档仅保留作迁移历史；当前部署和运行链路以
`backend_py` 和 [docs/fastapi-backend.md](docs/fastapi-backend.md) 为准。

任务流程固定为：`search -> transfer -> strm`

## 技术栈

- Frontend: React + Vite + TypeScript + Ant Design
- Backend: FastAPI + Python
- Database: SQLite
- Log streaming: SSE

## 功能概览

- 前端输入关键词并搜索资源
- 后端通过 PanSou 搜索资源并按 115 分享身份去重
- 前端展示统一 DTO 的资源列表
- 用户可单选或多选资源后提交单任务/批量任务
- 后端通过 p115 adapter 转存到 115
- 转存成功后由内置 STRM 服务生成播放链接文件
- 前端通过 SSE 实时显示任务日志和状态
- SQLite 持久化任务、日志和搜索历史

## 项目结构

```text
strmallinone/
├── backend_py/              # 当前运行后端
│   ├── app/api/
│   ├── app/adapters/
│   ├── app/repositories/
│   ├── app/services/
│   └── tests/
├── backend/                 # 旧 TypeScript 后端，仅作迁移参考
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

### 当前 FastAPI 后端分层

- `api`: 参数校验、批次/任务路由和 SSE
- `services`: 搜索去重、批次 worker、单项工作流和 STRM 编排
- `adapters`: PanSou、p115、AList 外部接口
- `repositories`: SQLite 任务、批次、日志和搜索历史持久化

### 核心服务

- `SearchService`: PanSou 搜索结果去重并写入 `search_history`
- `BatchService`: 批量输入去重、幂等复用和有界 worker
- `WorkflowService`: 串行执行 `transfer -> strm`
- `TaskLogService`: 统一写日志并推送 SSE

## 环境变量

复制 [backend_py/.env.example](backend_py/.env.example) 为 `backend_py/.env`。

当前运行链路需要 PanSou、p115 Cookie、AList 和 STRM 配置；变量说明见
[docs/fastapi-backend.md](docs/fastapi-backend.md)。

下面的 CloudSaver 变量仅供旧 TypeScript 后端迁移参考，不参与当前 Docker 运行。

### 旧 TypeScript 环境变量（历史参考）

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
cd backend_py
PYTHONPATH=.. uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
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
- [backend_py/Dockerfile](backend_py/Dockerfile)
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
- 后端容器直接运行 FastAPI/uvicorn
- SQLite 数据通过卷挂载到宿主机目录 `./backend_py/data`
- 容器启动时会读取根目录 `.env` 或 `backend_py/.env`

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

### `POST /api/batches/transfer`

批量提交搜索结果，`concurrency` 会限制在 1 到 4，默认 2。使用
`GET /api/batches/:batchId` 和 `GET /api/batches/:batchId/items` 查看聚合进度和
失败项；详见 [docs/batch-transfer.md](docs/batch-transfer.md)。

## SQLite 表

- `transfer_tasks`
- `task_logs`
- `search_history`
- `transfer_batches`
- `transfer_items`

数据库默认写到 `backend_py/data/app.db`（Docker 使用 `./backend_py/data`）。

## 历史 TypeScript 后端（不参与当前运行）

以下内容只用于迁移参考；当前 Docker 和本地 FastAPI 启动方式以上文为准。

## 旧版真实接口替换点

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
