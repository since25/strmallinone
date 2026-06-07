# Manual 115 Transfer Design

## Goal

Add a manual 115 transfer entry point for resources that do not come from the PanSou search API. A user can paste a full 115 share text, choose either movie or TV, and create the same transfer-to-STRM task used by search results.

## Scope

- Accept a pasted share text that contains a 115 share link and extraction code.
- Support `movie` and `tv` destination selection using the existing media type model.
- Reuse the current task repository, task logs, p115 transfer adapter, and STRM generation workflow.
- Keep PanSou search behavior unchanged.

## User Flow

1. The user opens the existing workflow console.
2. The user pastes a full 115 share text into a manual transfer form.
3. The user selects movie or TV.
4. The user starts the manual task.
5. The UI shows the new task ID, current task status, and live logs in the existing right-side panels.

## Backend Design

Add a dedicated manual task endpoint:

```text
POST /api/tasks/manual-transfer
```

Request body:

```json
{
  "shareText": "115 share text containing a link and extraction code",
  "mediaType": "movie"
}
```

The endpoint parses the share text into:

- `shareUrl`
- `shareCode`
- `receiveCode`

It then creates a `ResourceDto` with:

- `provider`: `115`
- `mediaType`: request value
- `rawType`: `video`
- `size`: `-`
- `extra.source`: `manual`
- `extra.shareCode`: parsed share code
- `extra.receiveCode`: parsed extraction code

The endpoint creates a normal task and calls `WorkflowService.run(task_id, resource)`, matching the existing search-result transfer endpoint.

## Parsing Rules

The parser should accept full pasted text, not only a bare URL. It should find a 115 share URL containing `/s/<shareCode>`.

The receive code can come from:

- A `password=` query parameter in the URL.
- Common Chinese share text patterns such as `提取码：abcd`, `访问码 abcd`, or `密码: abcd`.

If the link or receive code cannot be found, the endpoint returns a validation error and does not create a task.

## Frontend Design

Add a manual transfer panel near the existing search controls. The panel contains:

- A multiline input for full 115 share text.
- A movie/TV selector.
- A button to create the manual transfer task.

On success, the page stores the returned task ID in the same state currently used by search-result tasks. Existing polling, task status, and log streaming continue to work without new display components.

## Error Handling

- Empty share text: show a required-field error.
- Missing 115 link or extraction code: backend returns a clear error, frontend displays it through the existing message system.
- Transfer or STRM failures after task creation: existing workflow status and logs report the failure.

## Tests

Backend tests should cover:

- Parsing a URL with `password=`.
- Parsing full Chinese share text with `提取码`, `访问码`, or `密码`.
- Rejecting text that has no valid receive code.
- Creating a manual transfer task with the expected resource shape and media type.

Frontend verification should cover:

- Manual form validation.
- Successful task creation updates the active task ID.
- The existing task status and log panels still display the manual task.
