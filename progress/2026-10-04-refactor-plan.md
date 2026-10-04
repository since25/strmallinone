## 2026-10-04 - Task: Create staged batch transfer refactor plan

### What was done

- 梳理当前 FastAPI 运行链路、旧 TypeScript 后端边界、任务状态和 STRM 生成流程。
- 将资源去重、任务幂等、批次模型、有界 worker、前端多选和验收拆成五个可验证阶段。
- 明确单任务 API 兼容、SQLite 增量迁移、并发上限、重复资源处理和回滚策略。

### Testing

- 只读检查了 `backend_py`、`backend`、`frontend`、`docker-compose.yml` 和现有测试布局。
- 计划文档完成结构检查；尚未执行施工代码验证。

### Notes

Changed files:
- `docs/superpowers/plans/2026-10-04-batch-transfer-refactor.md`: 新增分阶段实施计划。

Rollback:
- 删除本轮新增计划文档和进度记录即可回到计划落地前状态；未修改业务源码。
