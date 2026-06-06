# FastAPI + p115 + STRM Backend Redesign

## Goal

Replace the current Node/Express backend and CloudSaver dependency with a Python backend built around FastAPI, PanSou, p115, AList, and built-in STRM generation.

The React frontend should continue to work against the existing API surface as much as possible. Frontend copy and UI refinements can happen later.

The deployed service is expected to keep running through Docker on server `192.168.70.197`.

## Current State

The current backend exposes:

- `GET /api/health`
- `POST /api/search`
- `POST /api/tasks/transfer`
- `GET /api/tasks/:taskId`
- `GET /api/tasks/:taskId/logs`
- `GET /api/tasks/:taskId/logs/stream`

Search currently combines CloudSaver and PanSou. Transfer currently calls CloudSaver for the 115 save flow. STRM generation is currently delegated to a separate `since25/strm_webhook` Flask service through HTTP.

This creates two avoidable dependencies:

- CloudSaver is used for both search and 115 transfer, but PanSou search is more accurate and overlaps the useful 115 results.
- STRM generation is a separate service even though its logic is small and can become part of the backend workflow.

## Target Architecture

The backend becomes a FastAPI application:

```text
Frontend
  -> FastAPI backend
      -> PanSou adapter: search only
      -> p115 adapter: 115 Cookie based share receive/save
      -> AList adapter: refresh/list visible media paths
      -> STRM service: generate .strm files pointing to AList /d URLs
      -> SQLite repositories: tasks, logs, search history
      -> SSE endpoint: live task logs
```

CloudSaver is fully removed from the runtime workflow.

## API Compatibility

FastAPI should preserve the current frontend-facing routes:

- `GET /api/health`
- `POST /api/search`
- `POST /api/tasks/transfer`
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/logs`
- `GET /api/tasks/{task_id}/logs/stream`

The request and response shapes should stay compatible with the existing frontend types wherever practical:

- Search still returns `ResourceDto[]`.
- Resources still use provider `115`.
- Resource metadata still includes `shareCode`, `receiveCode`, `shareUrl`, and source fields.
- Transfer task creation still returns `{ taskId }`.
- Task status still exposes `status`, `transferStatus`, `strmStatus`, and `errorMessage`.

FastAPI may also expose compatibility routes for the old STRM service:

- `POST /webhook/strm`
- `POST /webhook/strm/direct`

These are optional for internal workflow, but useful during migration and for manual testing.

## Search Design

Search uses PanSou only.

Flow:

1. `POST /api/search` receives `keyword`, `driver`, and `mediaType`.
2. The backend calls PanSou's native search API with `kw` and `cloud_types: ["115"]`.
3. The PanSou mapper reads `merged_by_type["115"]`.
4. Each result is normalized into the existing `ResourceDto` shape.
5. Invalid or unparsable 115 links are skipped.
6. Search history is written to SQLite.

CloudSaver search is not called as fallback. If PanSou fails, the API returns a search failure so the user sees the real dependency state.

## p115 Transfer Design

Transfer uses a p115-backed Python adapter and a 115 Cookie provided through configuration.

Configuration:

- `P115_COOKIE`
- `P115_DEFAULT_MOVIE_FOLDER`
- `P115_DEFAULT_TV_FOLDER`
- `P115_ROOT_PATH` or equivalent folder mapping
- optional timeout and retry settings

Flow:

1. Transfer receives a normalized PanSou 115 resource.
2. The adapter validates `shareCode` and `receiveCode`.
3. The adapter reads share info through p115.
4. The adapter finds or resolves the configured target folder.
5. The adapter receives/saves the shared files into the target folder.
6. The adapter returns a normalized transfer result:

```json
{
  "success": true,
  "message": "115 transfer succeeded",
  "data": {
    "savePath": "/115/automv/example",
    "sourceName": "example",
    "savedName": "example",
    "fileCount": 1,
    "transferId": "..."
  },
  "raw": {}
}
```

The service should treat already-saved resources as successful when p115/115 reports a duplicate or already-received state.

## AList And STRM Design

AList remains part of the playback chain because Emby reads STRM files whose contents point to AList `/d` URLs, and AList returns the final playable 302 URL.

Transfer success is not the end of the task. The workflow must wait for AList to see the transferred files and then generate STRM files.

Flow:

1. p115 transfer returns an expected AList path, such as `/115/automv/example`.
2. The workflow waits for a configurable delay.
3. The AList adapter calls `/api/fs/list` with `refresh: true`.
4. The STRM service resolves the actual AList path. It should preserve the current `strm_webhook` behavior:
   - recursive path resolution,
   - fuzzy matching for path segment differences,
   - recursive directory traversal,
   - direct file mode when a file list is known,
   - video extension filtering,
   - skip existing STRM files.
5. STRM files are written under `STRM_SAVE_DIR`.
6. Each STRM file contains a URL based on `STRM_SERVER`, normally ending in `/d`, plus the URL-encoded AList path.

Configuration:

- `ALIST_URL`
- `ALIST_TOKEN`
- `STRM_SERVER`
- `STRM_SAVE_DIR`
- `STRM_REPLACE_PATH`
- `STRM_DELAY_SECONDS`
- `STRM_VIDEO_EXTS`

## Workflow Design

The task workflow becomes:

```text
create task
  -> running
  -> PanSou resource already selected by frontend
  -> p115 transfer
  -> AList refresh/list confirmation
  -> STRM generation
  -> success or failed
```

Task logs should clearly show each stage:

- task created
- transfer started
- p115 share info loaded
- target folder resolved
- 115 transfer succeeded or duplicate detected
- waiting for AList refresh
- AList path resolved
- STRM generation started
- STRM generated, skipped, and failed counts
- task completed or failed

## Proposed Python Layout

```text
backend_py/
  app/
    main.py
    config.py
    api/
      health.py
      search.py
      tasks.py
      strm_compat.py
    adapters/
      pansou.py
      p115_adapter.py
      alist.py
    services/
      search_service.py
      transfer_service.py
      workflow_service.py
      strm_service.py
      task_log_service.py
      task_log_stream.py
    repositories/
      database.py
      task_repository.py
      task_log_repository.py
      search_history_repository.py
    models/
      resource.py
      task.py
      strm.py
```

The old Node backend can remain in the repository during migration, but the Docker Compose runtime should switch the backend service to FastAPI once parity is reached.

## Docker Design

Docker should keep a simple deployment path for server `192.168.70.197`:

- `frontend`: unchanged Vite build served by nginx.
- `backend`: FastAPI app served by uvicorn.
- SQLite data volume remains mounted from the host.
- STRM save directory is mounted from the host path used by the media stack.

The backend image needs Python dependencies:

- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`
- `aiosqlite` or synchronous SQLite support
- `p115client` or the selected p115 package

If the selected p115 package is easier to use synchronously, the FastAPI workflow can run blocking p115 work inside a background task or thread executor.

## p115 Package Validation

The migration should start with a small p115 validation spike before the full backend is replaced. The spike must prove these operations with a real Cookie:

1. Load the authenticated 115 client from `P115_COOKIE`.
2. Read share information from `shareCode` and `receiveCode`.
3. Resolve or create/find the configured target folder.
4. Save the shared files into that folder.
5. Return enough file and folder metadata for the workflow to build the expected AList path.

If the selected package cannot provide all five operations reliably, the implementation should stop at this checkpoint and choose a different p115 package or a direct 115 API adapter before continuing.

## Migration Strategy

1. Validate the selected p115 package with a real Cookie and one known 115 share.
2. Add the new FastAPI backend beside the current backend.
3. Recreate the existing API contract and SQLite schema behavior.
4. Implement PanSou-only search.
5. Implement p115 transfer.
6. Port STRM generation from `since25/strm_webhook`.
7. Wire the full task workflow.
8. Switch Docker Compose backend service from Node to FastAPI.
9. Remove CloudSaver runtime configuration and docs references after parity is verified.

## Verification Plan

Minimum checks:

- FastAPI unit tests for PanSou mapping and 115 link parsing.
- p115 adapter tests with mocked p115 responses.
- STRM service tests for:
  - direct file mode,
  - directory traversal,
  - path replacement,
  - skipping existing files,
  - video extension filtering.
- API compatibility tests for current frontend routes.
- Docker build for backend and frontend.

Manual server validation:

1. Configure `P115_COOKIE`, PanSou, AList, and STRM variables.
2. Search a known keyword through the frontend.
3. Create a transfer task.
4. Confirm the resource appears in 115 and AList can list the path.
5. Confirm STRM files are generated.
6. Confirm Emby can play through the AList 302 path.

## Confirmed Decisions

This design fixes these decisions:

- The frontend route and DTO contract should stay stable during the backend migration.
- AList remains required because playback still depends on AList 302 URLs.
- STRM generation should be built into FastAPI rather than kept as a separate Flask service.
- CloudSaver should be removed completely from runtime search and transfer.
