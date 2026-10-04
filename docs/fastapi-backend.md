# FastAPI Backend Migration Notes

当前后端迁移目标是将旧的 CloudSaver/Express 链路替换为 `FastAPI + PanSou + p115 + AList/STRM` 一体化服务。

## Current Flow

```text
frontend
  -> POST /api/search
  -> PanSou native API
  -> POST /api/tasks/transfer
  -> p115 Cookie transfer
  -> wait for AList visibility
  -> built-in STRM generation
  -> Emby reads AList /d URLs from generated .strm files
```

CloudSaver is no longer part of search or transfer in the Python backend.

## Batch transfer and idempotency

`backend_py` is the runtime backend. Search results are de-duplicated by
`provider:shareCode:receiveCode`; the first title is retained and distinct
source labels are exposed in `extra.sources`.

Single task creation remains available at `POST /api/tasks/transfer` and
`POST /api/tasks/manual-transfer`. Both routes return `taskId` and `reused`.
An active or successful task with the same resource key and target folder is
reused. Failed tasks may be submitted again.

Batch creation uses `POST /api/batches/transfer`. `concurrency` is clamped to
1–4 and defaults to 2. Inspect a batch with `GET /api/batches/{batch_id}` and
its children with `GET /api/batches/{batch_id}/items`. A batch is `success`
when all children succeed or are skipped, `partial` when some succeed and some
fail, and `failed` when every child fails. Duplicate p115 receives are
successful item operations and are counted as `skipped`.

The SQLite migration is additive. `transfer_tasks` stores the resource key,
target folder, duplicate flag and retry count; `transfer_batches` and
`transfer_items` store durable batch state. After a restart, query the batch
endpoint to inspect persisted children. Pending/running work does not resume
automatically in this release; retry unfinished items through the single-task
route.

Reused pending/running items wait up to 30 seconds for the existing task to
reach a terminal state. This prevents a worker from hanging forever on work
left by a previous process; timed-out items are marked failed for resubmission.

Transient adapter failures (timeouts, connection errors, 429/5xx) are retried
up to two times per batch item. Invalid parameters, credentials, share codes,
permissions and missing folders are treated as permanent failures.

## Share Code And Receive Code

`shareCode` is the 115 share id in the share URL path.

`receiveCode` is the 115 extraction/password code.

Example:

```text
https://115.com/s/abc123?password=xyzw
```

- `shareCode`: `abc123`
- `receiveCode`: `xyzw`

The backend can parse these from `shareUrl`, so the frontend does not need to ask the user to split them manually. PanSou mapping also fills `extra.shareCode` and `extra.receiveCode` when the source data contains enough information.

## Environment

The Python backend reads environment variables from:

1. root `.env`
2. `backend_py/.env`
3. process/container environment

`backend_py/.env` can override root `.env`. Secrets are intentionally not committed.

Use `backend_py/.env.example` as the non-secret template. The important production values are:

```env
P115_COOKIE=
PANSOU_BASE_URL=http://192.168.70.120:8888
ALIST_URL=http://192.168.70.138:5244
ALIST_TOKEN=
STRM_SERVER=http://192.168.70.138:5244/d
STRM_SAVE_DIR=/data/strm
```

## Docker

The compose backend service now builds `backend_py/Dockerfile` and runs FastAPI on port `3000`.

```bash
docker compose up -d --build
```

Persistent paths:

- `./backend_py/data:/data/backend`
- `./strm_output:/data/strm`

On the server, keep the root `.env` alongside `docker-compose.yml`, or create `backend_py/.env` if you want Python-only overrides.

## Compatibility Routes

The FastAPI backend keeps the old STRM webhook shapes:

- `POST /webhook/strm`
- `POST /webhook/strm/direct`

These are useful for manual migration checks and for old callers that still post directly to the STRM webhook path.

## Validation

Local automated tests:

```bash
cd backend_py
PYTHONPATH=. .venv/bin/pytest tests -q
```

Real p115 validation was performed with a local Cookie and a real 115 share link through `backend_py/scripts/p115_probe.py`. Do not commit the Cookie or share URL.
