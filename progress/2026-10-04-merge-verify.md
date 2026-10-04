## 2026-10-04 - Task: 合并批量转存分支并完成集成验证

### What was done

- 将批量转存后端分支 `codex/batch-transfer-refactor` 合并到 `main`，保留本轮重构后的前端实现。
- 修正手动转存 API 测试对后台协程调度时序的错误依赖，改为验证已持久化的任务资源数据。

### Testing

- `PYTHONPATH=. /tmp/strmallinone-verify-venv-merged-20261004/bin/pytest tests -q`：54 passed。
- `node ../node_modules/typescript/bin/tsc -p tsconfig.json --pretty false`：通过。
- `node ../node_modules/vite/bin/vite.js build --config vite.config.ts`：通过；仅有产物体积提示。
- `git diff --check`：通过。

### Notes

Changed files:
- `backend_py/tests/test_tasks_api.py`: 用任务详情验证手动分享文本解析结果。
- `progress/2026-10-04-merge-verify.md`: 记录合并和验证结果。

Rollback:
- 回退集成提交和本轮验证提交即可恢复合并前的分支状态；部署前保留当前镜像作为回滚点。
