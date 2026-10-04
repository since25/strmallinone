# Batch Transfer And Deduplication Refactor Implementation Plan

> 状态：已授权实施；日期：2026-10-04；依据：当前 `backend_py` 运行链路、现有 SQLite 任务模型和前端单选流程；适用范围：资源搜索去重、单任务幂等、批量转存、批次进度与运行文档；若后续计划被替代，以新的带日期计划为准。

> **For agentic workers:** When implementation is authorized, execute task-by-task in the current session by default. Use subagent-driven-development only when delegation is explicitly enabled and available. A plan-only request ends with this plan. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将运行时统一到 FastAPI，在保持现有单任务接口兼容的基础上，补齐资源去重、任务幂等、批量转存、批次进度和可恢复执行能力。

**Architecture:** 以 `backend_py` 为唯一运行后端，先把资源身份和任务状态抽成稳定的领域约定，再在其上增加“批次 + 子任务”模型。批次通过有界 worker 执行现有 `transfer -> STRM` 单项工作流，外部 p115/AList 继续由 adapter 封装；旧 TypeScript 后端仅保留为迁移历史，不再接收新业务逻辑。

**Tech Stack:** FastAPI, Pydantic, SQLite, asyncio, React, Vite, TypeScript, Ant Design, pytest。

## Global Constraints

- 运行入口保持 `docker-compose.yml -> backend_py/Dockerfile`，不恢复 CloudSaver 运行链路。
- 保持现有 `POST /api/search`、`POST /api/tasks/transfer`、任务详情、日志和 STRM 兼容接口的响应形状。
- 资源唯一身份使用 `provider + shareCode + receiveCode`，任务去重额外包含目标目录。
- 批量执行必须使用有界并发；默认并发为 2，允许请求覆盖但必须限制在 1 到 4。
- 重复资源标记为 `skipped` 或返回已有任务，不重复调用 p115 转存。
- p115 返回“已接收/无需重复接收”时视为成功且 `duplicate=true`。
- 不把 Cookie、token、真实分享链接或真实业务数据写入代码、测试夹具、日志或文档。
- 每个任务阶段必须有自动化验证；完成后追加一轮 `progress/` 日志。

## Stage 1: Resource Identity And Search Deduplication

**Deliverable:** 搜索结果按标准资源键去重，保留来源信息；旧单任务接口继续可用。

**Files:**
- Create: `backend_py/app/services/resource_identity.py`
- Modify: `backend_py/app/services/search_service.py`
- Modify: `backend_py/app/models/resource.py`
- Test: `backend_py/tests/test_resource_identity.py`
- Test: `backend_py/tests/test_pansou_search.py`

**Interfaces:**
- `resource_key(resource: ResourceDto) -> str`
- `target_folder(resource: ResourceDto, movie_folder: str, tv_folder: str) -> str`
- `dedupe_resources(resources: list[ResourceDto]) -> list[ResourceDto]`

- [x] **Step 1: Add failing tests** for identical share/code with different titles, different receive codes, and source aggregation.
- [x] **Step 2: Implement canonical key and stable first-result deduplication.** Preserve the first title and add `extra.sources` as a unique list.
- [x] **Step 3: Use the helper from `SearchService.search`.** Persist the deduplicated result count to `search_history`.
- [x] **Step 4: Run:** `PYTHONPATH=. pytest tests/test_resource_identity.py tests/test_pansou_search.py -q`.
- [x] **Step 5: Append verification and rollback point to `progress/`.

## Stage 2: Task Idempotency And Durable State

**Deliverable:** 相同资源在相同目标目录下不会重复创建活动任务；数据库具备可查询的幂等键。

**Files:**
- Modify: `backend_py/app/repositories/database.py`
- Modify: `backend_py/app/repositories/task_repository.py`
- Modify: `backend_py/app/api/tasks.py`
- Modify: `backend_py/app/models/task.py`
- Test: `backend_py/tests/test_repositories.py`
- Test: `backend_py/tests/test_tasks_api.py`

**Interfaces:**
- `TaskRepository.create_or_get(...) -> tuple[TaskDto, bool]`
- `TaskRepository.find_active_by_resource_key(resource_key: str, target_folder: str) -> TaskDto | None`

- [x] **Step 1: Add failing repository/API tests** for duplicate pending tasks, existing success tasks, and failed-task retry.
- [x] **Step 2: Add an idempotency migration** for `resource_key`, `target_folder`, and `retry_count`; create an index that supports active-task lookup without deleting existing rows.
- [x] **Step 3: Implement `create_or_get`.** Return an existing pending/running/success task; allow a new task after failure.
- [x] **Step 4: Update both normal and manual transfer endpoints** to calculate the same key and return `{ taskId, reused }` while preserving the existing `taskId` field.
- [x] **Step 5: Run:** `PYTHONPATH=. pytest tests/test_repositories.py tests/test_tasks_api.py -q`.
- [x] **Step 6: Append verification and rollback point to `progress/`.

## Stage 3: Batch Model, Bounded Workers, And Batch API

**Deliverable:** 支持一次提交多个资源，批次内限并发执行，单项失败不影响其他项，服务重启后可查询已落库状态。

**Files:**
- Create: `backend_py/app/models/batch.py`
- Create: `backend_py/app/repositories/batch_repository.py`
- Create: `backend_py/app/services/batch_service.py`
- Modify: `backend_py/app/api/tasks.py`
- Modify: `backend_py/app/main.py`
- Modify: `backend_py/app/repositories/database.py`
- Test: `backend_py/tests/test_batch_service.py`
- Test: `backend_py/tests/test_tasks_api.py`

**Interfaces:**
- `POST /api/batches/transfer` with `{ keyword, items, concurrency? }`
- `GET /api/batches/{batch_id}`
- `GET /api/batches/{batch_id}/items`
- `BatchService.create_batch(...) -> BatchDto`
- `BatchService.run(batch_id) -> None`

- [x] **Step 1: Add failing tests** for input deduplication, active-task reuse, bounded concurrency, partial failure, and aggregate counts.
- [x] **Step 2: Add `transfer_batches` and `transfer_items` tables** with foreign keys, aggregate counters, item status, error, duplicate flag, and retry count.
- [x] **Step 3: Implement batch creation.** Normalize and deduplicate input, create one child item per pending resource, and record skipped/reused items.
- [x] **Step 4: Implement a bounded worker pool.** Use `asyncio.Queue`, default concurrency 2, clamp request values to 1..4, and reuse the current single-item workflow.
- [x] **Step 5: Persist state before and after each external side effect.** Classify invalid input as permanent failure and retry only transient adapter failures up to the configured limit.
- [x] **Step 6: Add batch status and item endpoints.** Keep single-task endpoints unchanged.
- [x] **Step 7: Run:** `PYTHONPATH=. pytest tests/test_batch_service.py tests/test_tasks_api.py -q`.
- [x] **Step 8: Append verification and rollback point to `progress/`.

## Stage 4: Frontend Multi-Select And Progress

**Deliverable:** 搜索结果支持多选，用户可以创建批量任务并看到批次进度；单条转存入口继续可用。

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/components/TaskStatusCard.tsx`
- Modify: `frontend/src/styles.css`

- [x] **Step 1: Add API/types** for batch creation, batch detail, and batch items.
- [x] **Step 2: Change the results table to controlled multi-select.** Keep selected resources stable when pagination changes.
- [x] **Step 3: Add a batch action** that validates at least one selection, creates the batch, and polls batch status.
- [x] **Step 4: Display total, running, success, skipped, and failed counts; expose failed item task IDs for retry through the existing single-task view.
- [x] **Step 5: Run:** `npm run build --workspace frontend` and the relevant frontend type checks.
- [x] **Step 6: Append verification and rollback point to `progress/`.

## Stage 5: Documentation, Recovery, And Whole-Branch Verification

**Deliverable:** 运行文档、API 示例、迁移说明和验证记录与实现一致。

**Files:**
- Modify: `README.md`
- Modify: `docs/fastapi-backend.md`
- Create: `docs/batch-transfer.md`
- Create: `progress/2026-10-04-batch-transfer-refactor.md`

- [x] **Step 1: Document the runtime architecture, resource key, task idempotency, batch states, concurrency limit, and retry behavior.**
- [x] **Step 2: Remove or clearly label stale CloudSaver instructions in user-facing runtime documentation.**
- [x] **Step 3: Add recovery guidance** for restarting the service and inspecting unfinished batches.
- [x] **Step 4: Run the backend suite, frontend build, Python compile check, and API contract checks. Record any environment-only failures separately.**
- [x] **Step 5: Have Astra perform final whole-branch acceptance against this plan and the actual diff.**

## Rollback Strategy

- Each stage is isolated by schema/API boundary and can be reverted independently.
- Before Stage 2, rollback is code-only.
- Before Stage 3, preserve old task columns and make new tables additive.
- If batch execution is disabled, single-task APIs continue to use the existing workflow.
