# 批量转存说明

状态：实施版（2026-10-04）。适用范围：FastAPI 批量转存、资源去重和任务幂等。

## 架构

```text
React 多选 -> POST /api/batches/transfer -> transfer_batches/items
         -> 有界 worker（默认 2，范围 1..4）
         -> 单项 transfer -> STRM 工作流
         -> GET /api/batches/{id} 查看聚合进度
```

资源身份为 `provider + shareCode + receiveCode`，任务身份在此基础上增加
目标目录。相同资源在同一目标目录下如果已有 `pending/running/success`
任务，会复用该任务；失败任务允许重新提交。

## API

批量请求的 `items` 使用搜索接口返回的资源 DTO，`concurrency` 可省略：

```http
POST /api/batches/transfer
```

```json
{"keyword":"demo","items":[],"concurrency":2}
```

返回的 `data.id` 是批次 ID。使用以下接口读取状态：

```http
GET /api/batches/{batch_id}
GET /api/batches/{batch_id}/items
```

单任务接口仍保持原有路径和 `taskId` 字段，额外返回 `reused` 表示是否命中
幂等记录。

## 重复和失败处理

- 搜索阶段保留第一条标题，并合并 `extra.sources`。
- 批次输入先去重，再为每个唯一资源建立子项。
- 已有任务的子项标记为 `skipped`，不会再次调用 p115。
- p115 返回“已接收/无需重复接收”时任务成功，子项计入 `skipped`。
- 单项失败只影响该子项；批次最终状态会变为 `partial` 或 `failed`。
- 网络超时、连接异常、429/5xx 和明确的临时错误最多自动重试 2 次；参数、权限、分享码和目录错误直接失败。
- 已有 `pending/running` 任务的子项会等待该任务进入终态；已有成功任务才会立即标记 `skipped`。
- 复用任务等待最多 30 秒；服务重启留下的未接管任务超时后子项失败并提示重新提交，worker 不会永久阻塞。

## p115 分享内容限制

适配器会逐项接收分享中的文件并为每个文件返回 `savePaths`，工作流会逐个
生成 STRM。多个分享条目中包含目录时会明确失败并显示“不支持目录递归转存”，
不会再静默只处理第一项；单条目分享仍按原有接收流程处理，以保持现有兼容性。

## 重启恢复

批次、子项和任务状态都在 SQLite 中落库。服务重启后可以继续查询批次和
子项，确认失败项的 `taskId` 后通过单任务接口重新提交。当前版本不会在
进程启动时自动接管中断中的 worker，因此生产环境建议先检查运行中的批次，
再按失败项重试。
