## 2026-10-04 - Task: Implement batch transfer and deduplication refactor

### What was done

- Added stable resource identity helpers and search result de-duplication with source aggregation.
- Added additive SQLite fields and task repository idempotency lookup/create-or-get behavior; preserved single-task routes and added `reused`.
- Added durable batch/item models and repositories, bounded worker execution, batch status/item APIs, and duplicate-aware aggregate counts.
- Updated the React console for controlled multi-select, batch creation, and batch progress polling while retaining single-task controls.
- Updated FastAPI/README runtime documentation and added batch transfer recovery guidance.
- Added migration backfill for pre-existing task identities, terminal-state waiting for reused tasks, bounded transient retries, failed-item viewing/retry controls, and explicit p115 multi-file handling.

### Testing

- `PYTHONPATH=. python3 -m compileall -q backend_py/app backend_py/tests` passed.
- `git diff --check` passed.

## 2026-10-04 - Task: Final acceptance cleanup

### What was done

- Added orphan-task compensation coverage and stale reused-task failure transition.
- Updated the plan checkboxes for completed Stage 1–5 implementation and validation steps.
- Corrected the README's current runtime sections and clarified the p115 directory compatibility wording.

### Testing

- Targeted tests: 16 passed.
- Python compile check: passed.
- `git diff --check`: passed.
- Generated `__pycache__` directories were removed and ignored by `.gitignore`.

## 2026-10-04 - Task: Final documentation wording cleanup

### What was done

- Updated the frontend hero copy to describe the current PanSou → p115 → AList/STRM chain.
- Added a clear historical-reference warning to `docs/development-guide.md` with links to the current FastAPI and batch documents.
- Closed the missing Markdown emphasis marker in the Stage 5 plan checklist.

### Testing

- `git diff --check` passed.
- Static text checks confirmed the current UI wording and historical warning are present.
- `PYTHONPATH=. pytest backend_py/tests/test_repositories.py backend_py/tests/test_pansou_search.py backend_py/tests/test_tasks_api.py -q` could not collect because the environment lacks `httpx`/`httpx2`.
- `npm run build --workspace frontend` could not run because the environment lacks the `tsc` executable (`node_modules` is unavailable).
- Added `backend_py/tests/test_resource_identity.py` and `backend_py/tests/test_batch_service.py`; dependency absence prevented collection in this environment.

### Notes

Changed files:
- `backend_py/app/services/resource_identity.py`: resource keys, target folders, and stable de-duplication.
- `backend_py/app/repositories/database.py`, `task_repository.py`, `batch_repository.py`: additive schema and durable state.
- `backend_py/app/models/batch.py`, `task.py`, `services/batch_service.py`, `api/tasks.py`: batch API and worker orchestration.
- `frontend/src`: multi-select batch action and status polling.
- `README.md`, `docs/fastapi-backend.md`, `docs/batch-transfer.md`: runtime and recovery documentation.

Rollback:
- Revert the implementation files and remove the additive batch tables/columns through the existing SQLite database backup; single-task route code remains isolated in `tasks.py`.

## 2026-10-04 - Task: Address Astra acceptance findings

### What was done

- Added legacy task identity backfill and additive batch item `reused` state.
- Reused pending/running tasks now wait for terminal state; reused successful tasks are skipped with accurate batch counts.
- Added transient error classification and two retry attempts with task/item retry counters; permanent input, permission and share errors fail directly.
- Made batch creation compensate by deleting partially-created batch rows on item persistence errors and clamped API concurrency to 1..4.
- Added failed batch-item viewing/retry controls and explicit p115 multi-file processing; directory shares fail with a clear limitation message.
- Added resource identity, batch retry/clamping, and legacy task idempotency tests.

### Testing

- `PYTHONPATH=. python3 -m compileall -q backend_py/app backend_py/tests` passed.
- `PYTHONPATH=. pytest backend_py/tests/test_resource_identity.py backend_py/tests/test_batch_service.py backend_py/tests/test_task_idempotency.py -q` passed (13 tests).
- Full backend collection remains blocked by missing `httpx`/`httpx2` and `p115client`; frontend build remains blocked by missing `tsc`.
- `git diff --check` passed.
- Targeted batch/idempotency/resource tests pass (15 tests), including transient retry and reused-task timeout coverage.

## 2026-10-04 - Task: Close remaining acceptance findings

### What was done

- Batch compensation now records only `reused=False` task IDs and deletes their untouched pending rows when item persistence fails; reused tasks are retained.
- Reused-task timeout marks the stale pending/running task failed, allowing a later single-task submission to create a replacement.
- README main sections now describe FastAPI/PanSou/p115/AList, current Docker paths, current API/table names, and explicitly isolate old Express/CloudSaver material under historical headings.
- Clarified the p115 directory compatibility statement and added a repository compensation test.
- Added a `__pycache__` ignore rule and removed generated cache directories.

### Testing

- `PYTHONPATH=. pytest backend_py/tests/test_batch_service.py backend_py/tests/test_task_idempotency.py backend_py/tests/test_resource_identity.py -q` passed (16 tests).
- `PYTHONPATH=. python3 -m compileall -q backend_py/app backend_py/tests` passed; generated caches were removed afterward.
- `git diff --check` passed.
