# Manual 115 Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manual 115 share-text transfer entry point that creates the same transfer and STRM task used by PanSou search results.

**Architecture:** Backend parsing stays close to the existing PanSou 115 parsing code so both search and manual flows share rules. The manual API creates a normal `ResourceDto` and reuses the existing `WorkflowService.run()` path. The frontend adds a compact manual form that writes the returned task ID into the existing task status and log state.

**Tech Stack:** FastAPI, Pydantic, pytest, React, TypeScript, Ant Design.

---

## File Structure

- Modify `backend_py/app/adapters/pansou.py`: add a reusable `parse_115_share_text()` helper while preserving existing `parse_115_link()` behavior.
- Modify `backend_py/tests/test_pansou_search.py`: add parser tests for full manual share text.
- Modify `backend_py/app/api/tasks.py`: add `ManualTransferRequest` and `POST /tasks/manual-transfer`.
- Modify `backend_py/tests/test_tasks_api.py`: add API tests for manual task creation and invalid share text.
- Modify `frontend/src/types/index.ts`: add a request type for manual transfer task creation.
- Modify `frontend/src/api/client.ts`: add `createManualTransferTask()`.
- Modify `frontend/src/main.tsx`: add manual transfer form and submit handler.

---

### Task 1: Add Manual 115 Share Text Parsing

**Files:**
- Modify: `backend_py/tests/test_pansou_search.py`
- Modify: `backend_py/app/adapters/pansou.py`

- [ ] **Step 1: Write the failing parser tests**

Add these tests to `backend_py/tests/test_pansou_search.py` near the existing parser tests:

```python
from backend_py.app.adapters.pansou import PanSouClient, map_pansou_item, parse_115_share_text


def test_parse_115_share_text_uses_password_query():
    parsed = parse_115_share_text("分享 https://115cdn.com/s/sabc123?password=ABCD 复制即可")

    assert parsed == ("https://115cdn.com/s/sabc123?password=ABCD", "sabc123", "ABCD")


def test_parse_115_share_text_uses_chinese_extract_code():
    parsed = parse_115_share_text("资源链接：https://115.com/s/sxyz987\n提取码：t58d")

    assert parsed == ("https://115.com/s/sxyz987", "sxyz987", "t58d")


def test_parse_115_share_text_uses_access_or_password_label():
    assert parse_115_share_text("https://115.com/s/saaa111 访问码 efgh") == (
        "https://115.com/s/saaa111",
        "saaa111",
        "efgh",
    )
    assert parse_115_share_text("https://115.com/s/sbbb222 密码: WXYZ") == (
        "https://115.com/s/sbbb222",
        "sbbb222",
        "WXYZ",
    )


def test_parse_115_share_text_rejects_missing_receive_code():
    assert parse_115_share_text("https://115.com/s/sabc123") is None
```

- [ ] **Step 2: Run parser tests and verify red**

Run:

```bash
python -m pytest backend_py/tests/test_pansou_search.py::test_parse_115_share_text_uses_password_query backend_py/tests/test_pansou_search.py::test_parse_115_share_text_uses_chinese_extract_code backend_py/tests/test_pansou_search.py::test_parse_115_share_text_uses_access_or_password_label backend_py/tests/test_pansou_search.py::test_parse_115_share_text_rejects_missing_receive_code -v
```

Expected: FAIL with an import error for `parse_115_share_text`.

- [ ] **Step 3: Implement the parser helper**

In `backend_py/app/adapters/pansou.py`, replace the parser constants and `parse_115_link()` section with:

```python
LINK_RE = re.compile(r"(?P<url>https?://[^\s，。；;]+/s/(?P<share>[a-z0-9]+)(?:\?password=(?P<pwd>[A-Za-z0-9]{4}))?)", re.I)
CODE_RE = re.compile(r"(?:提取码|访问码|密码)\s*[:：]?\s*(?P<code>[A-Za-z0-9]{4})", re.I)


def parse_115_share_text(text: str, password: str | None = None) -> tuple[str, str, str] | None:
    match = LINK_RE.search(text.strip())
    if not match:
        return None
    receive_code = password or match.group("pwd")
    if not receive_code:
        code_match = CODE_RE.search(text)
        receive_code = code_match.group("code") if code_match else None
    if not receive_code:
        return None
    return match.group("url"), match.group("share"), receive_code


def parse_115_link(url: str, password: str | None = None) -> tuple[str, str] | None:
    parsed = parse_115_share_text(url, password)
    if not parsed:
        return None
    _, share_code, receive_code = parsed
    return share_code, receive_code
```

- [ ] **Step 4: Run parser tests and verify green**

Run the same command from Step 2.

Expected: PASS for all four parser tests.

- [ ] **Step 5: Run existing PanSou tests**

Run:

```bash
python -m pytest backend_py/tests/test_pansou_search.py -v
```

Expected: PASS, including existing `map_pansou_item` tests.

---

### Task 2: Add Manual Transfer API

**Files:**
- Modify: `backend_py/tests/test_tasks_api.py`
- Modify: `backend_py/app/api/tasks.py`

- [ ] **Step 1: Write failing API tests**

Add these tests to `backend_py/tests/test_tasks_api.py`:

```python
def test_create_manual_transfer_task_parses_share_text_and_returns_task_id():
    app = create_app()
    seen = {}

    async def fake_run(task_id, resource):
        seen["task_id"] = task_id
        seen["resource"] = resource
        app.state.task_log_service.append(task_id, "success", "fake manual workflow done")

    app.state.workflow_service.run = fake_run
    client = TestClient(app)

    response = client.post(
        "/api/tasks/manual-transfer",
        json={"shareText": "资源：https://115.com/s/sabc123\n提取码：t58d", "mediaType": "tv"},
    )

    assert response.status_code == 201
    task_id = response.json()["data"]["taskId"]
    task_response = client.get(f"/api/tasks/{task_id}")
    data = task_response.json()["data"]
    assert data["keyword"] == "手动 115 转存"
    assert data["resourceTitle"] == "手动 115 转存 sabc123"
    assert seen["resource"].mediaType == "tv"
    assert seen["resource"].shareUrl == "https://115.com/s/sabc123"
    assert seen["resource"].extra["source"] == "manual"
    assert seen["resource"].extra["shareCode"] == "sabc123"
    assert seen["resource"].extra["receiveCode"] == "t58d"


def test_create_manual_transfer_task_rejects_invalid_share_text():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/tasks/manual-transfer",
        json={"shareText": "只有链接 https://115.com/s/sabc123", "mediaType": "movie"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "未找到有效的 115 分享链接或提取码"
```

- [ ] **Step 2: Run API tests and verify red**

Run:

```bash
python -m pytest backend_py/tests/test_tasks_api.py::test_create_manual_transfer_task_parses_share_text_and_returns_task_id backend_py/tests/test_tasks_api.py::test_create_manual_transfer_task_rejects_invalid_share_text -v
```

Expected: FAIL with 404 for `/api/tasks/manual-transfer`.

- [ ] **Step 3: Implement the manual endpoint**

In `backend_py/app/api/tasks.py`, add this import:

```python
from ..adapters.pansou import parse_115_share_text
from ..models.resource import MediaType, ResourceDto
```

Replace the existing `ResourceDto` import line if needed so both `MediaType` and `ResourceDto` come from the same import.

Add this request model after `CreateTaskRequest`:

```python
class ManualTransferRequest(BaseModel):
    shareText: str
    mediaType: MediaType
```

Add this route after `create_transfer_task()`:

```python
@router.post("/tasks/manual-transfer", status_code=201)
async def create_manual_transfer_task(payload: ManualTransferRequest, request: Request):
    parsed = parse_115_share_text(payload.shareText)
    if not parsed:
        raise HTTPException(status_code=400, detail="未找到有效的 115 分享链接或提取码")
    share_url, share_code, receive_code = parsed
    task_id = f"task_{uuid4().hex[:10]}"
    resource = ResourceDto(
        id=f"manual_{share_code}_{receive_code}",
        title=f"手动 115 转存 {share_code}",
        provider="115",
        mediaType=payload.mediaType,
        rawType="video",
        size="-",
        shareUrl=share_url,
        extra={"source": "manual", "shareCode": share_code, "receiveCode": receive_code},
    )
    request.app.state.task_repository.create(task_id, "手动 115 转存", resource)
    request.app.state.task_log_service.append(task_id, "info", "手动 115 转存任务已创建，等待执行")
    asyncio.create_task(request.app.state.workflow_service.run(task_id, resource))
    return {"success": True, "data": {"taskId": task_id}}
```

- [ ] **Step 4: Run API tests and verify green**

Run the same command from Step 2.

Expected: PASS for both manual API tests.

- [ ] **Step 5: Run backend task and parser tests**

Run:

```bash
python -m pytest backend_py/tests/test_tasks_api.py backend_py/tests/test_pansou_search.py -v
```

Expected: PASS.

---

### Task 3: Add Frontend Manual Transfer Entry

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Add the API client type and function**

In `frontend/src/types/index.ts`, add:

```ts
export interface ManualTransferRequest {
  shareText: string;
  mediaType: MediaType;
}
```

In `frontend/src/api/client.ts`, update the import and add the function:

```ts
import type { ApiResponse, ManualTransferRequest, MediaType, ResourceItem, TaskDetail, TaskLogItem } from '../types';

export function createManualTransferTask(payload: ManualTransferRequest): Promise<{ taskId: string }> {
  return request<{ taskId: string }>('/api/tasks/manual-transfer', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
```

- [ ] **Step 2: Add the manual form state and handler**

In `frontend/src/main.tsx`, update the API import:

```ts
import { createManualTransferTask, createTransferTask, getTask, searchResources } from './api/client';
```

Add a form near the existing search form declaration:

```ts
const [manualForm] = Form.useForm<{ shareText: string; mediaType: MediaType }>();
```

Add this handler below `handleRunTask`:

```ts
const handleManualRunTask = async () => {
  const values = await manualForm.validateFields();
  setRunning(true);
  setTaskId(null);
  setTask(null);
  try {
    const result = await createManualTransferTask(values);
    setTaskId(result.taskId);
    messageApi.success(`手动任务已创建: ${result.taskId}`);
  } catch (error) {
    setRunning(false);
    messageApi.error(error instanceof Error ? error.message : '创建手动任务失败');
  }
};
```

- [ ] **Step 3: Render the manual transfer panel**

Add this `Card` between the search card and search result card in `frontend/src/main.tsx`:

```tsx
<Card title="手动 115 链接转存" className="panel-card">
  <Form form={manualForm} layout="vertical" initialValues={{ shareText: '', mediaType: 'movie' }}>
    <Form.Item
      name="shareText"
      label="完整分享文本"
      rules={[{ required: true, message: '请粘贴 115 分享文本' }]}
    >
      <Input.TextArea
        rows={4}
        placeholder="粘贴包含 115 链接和提取码的完整分享文本"
        allowClear
      />
    </Form.Item>
    <Row gutter={16} align="bottom">
      <Col xs={24} md={8}>
        <Form.Item name="mediaType" label="转存路径">
          <Select
            size="large"
            options={[
              { label: '电影', value: 'movie' },
              { label: '电视', value: 'tv' },
            ]}
          />
        </Form.Item>
      </Col>
      <Col xs={24} md={16}>
        <Form.Item label=" ">
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={running}
            onClick={() => void handleManualRunTask()}
            block
          >
            手动转存并生成 STRM
          </Button>
        </Form.Item>
      </Col>
    </Row>
  </Form>
</Card>
```

- [ ] **Step 4: Run frontend type/build verification**

Run:

```bash
npm run build --workspace frontend
```

Expected: PASS with TypeScript and Vite build succeeding.

---

### Task 4: End-to-End Verification

**Files:**
- No new file changes expected.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
python -m pytest backend_py/tests/test_pansou_search.py backend_py/tests/test_tasks_api.py -v
```

Expected: PASS.

- [ ] **Step 2: Run all Python backend tests**

Run:

```bash
python -m pytest backend_py/tests -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
npm run build --workspace frontend
```

Expected: PASS.

- [ ] **Step 4: Review changed files**

Run:

```bash
git diff -- backend_py/app/adapters/pansou.py backend_py/app/api/tasks.py backend_py/tests/test_pansou_search.py backend_py/tests/test_tasks_api.py frontend/src/types/index.ts frontend/src/api/client.ts frontend/src/main.tsx
```

Expected: Diff only contains manual 115 transfer parsing, API, tests, and UI changes.
