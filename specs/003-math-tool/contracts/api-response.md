# API Response Contract: Tool Invocation

**Endpoint**: `GET /api/conversations/{conversation_id}`

## ToolInvocationResponse (modified)

```json
{
  "id": "uuid",
  "tool_name": "calculate",
  "tool_input": "125 * 8",
  "tool_output": [],
  "tool_result": "1000",
  "created_at": "2026-04-07T12:00:00"
}
```

### Field Changes

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| tool_result | string, nullable | NEW | Raw output string from tool execution. `null` for legacy invocations without this field. |

### Examples by tool type

**calculate tool**:
```json
{
  "tool_name": "calculate",
  "tool_input": "sqrt(144) + 3**2",
  "tool_output": [],
  "tool_result": "21.0"
}
```

**calculate tool (error)**:
```json
{
  "tool_name": "calculate",
  "tool_input": "5 / 0",
  "tool_output": [],
  "tool_result": "Error: division by zero"
}
```

**web_search tool (unchanged behavior)**:
```json
{
  "tool_name": "web_search",
  "tool_input": "weather NYC",
  "tool_output": [
    { "title": "NYC Weather", "snippet": "Currently 72°F...", "url": "https://..." }
  ],
  "tool_result": "[{\"title\": \"NYC Weather\", ...}]"
}
```
