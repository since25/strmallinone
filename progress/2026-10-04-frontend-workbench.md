## 2026-10-04 - Task: 重构搜索与批量转存前端工作台

### What was done

- 将页面重组为搜索区、结果工作区和任务侧栏，移除渐变、毛玻璃和过大的圆角样式。
- 将搜索结果默认分页从 6 条调整为 20 条，并提供 20/50/100/200 条切换。
- 为结果表增加全选、反选和清空入口，接通多选批量转存和批次状态轮询。
- 保留单条转存、手动 115 转存、任务日志和失败项重试入口，并统一状态文案。

### Testing

- `node node_modules/typescript/bin/tsc -p frontend/tsconfig.json --pretty false` 通过。
- `node ../node_modules/vite/bin/vite.js build --config vite.config.ts`（在 `frontend/` 中执行）通过；仅有产物体积提示。
- `git diff --check` 通过。

### Notes

Changed files:
- `frontend/src/main.tsx`: 重做工作台布局、选择操作、分页和批次交互。
- `frontend/src/styles.css`: 使用简洁的浅色工作台样式。
- `frontend/src/api/client.ts`: 增加批次创建、查询和批次项查询接口类型。
- `frontend/src/types/index.ts`: 增加批次状态、批次项和任务扩展类型。
- `frontend/src/components/TaskStatusCard.tsx`: 重做任务和批次状态展示。
- `docs/frontend-workbench.md`: 记录新的前端行为和接口入口。

Rollback:
- 回退上述前端文件及 `docs/frontend-workbench.md`，即可恢复本轮前端改动；未修改后端源码。
