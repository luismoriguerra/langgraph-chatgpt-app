# SSE Event Contract: Chat Stream

**Endpoint**: `POST /api/conversations/{conversation_id}/chat`
**Transport**: Server-Sent Events (SSE)
**Format**: `data: {json}\n\n`

## Events

### text-delta (existing, unchanged)

```json
{ "type": "text-delta", "textDelta": "Hello" }
```

### tool-start (existing, unchanged)

```json
{ "type": "tool-start", "toolName": "calculate", "toolInput": "125 * 8" }
```

### tool-end (existing, unchanged)

```json
{ "type": "tool-end", "toolName": "calculate" }
```

### tool-result (NEW)

Emitted after `tool-end` for every tool invocation. Carries the raw string output from the tool execution.

```json
{ "type": "tool-result", "toolName": "calculate", "toolInput": "125 * 8", "result": "1000" }
```

For search tools:
```json
{ "type": "tool-result", "toolName": "web_search", "toolInput": "weather NYC", "result": "[{\"title\": ..., \"snippet\": ..., \"link\": ...}]" }
```

For errors (tool returned an error string):
```json
{ "type": "tool-result", "toolName": "calculate", "toolInput": "5 / 0", "result": "Error: division by zero" }
```

### sources (existing, unchanged)

```json
{ "type": "sources", "sources": [{ "title": "...", "snippet": "...", "url": "..." }] }
```

### finish (existing, unchanged)

```json
{ "type": "finish", "finishReason": "stop" }
```

### error (existing, unchanged)

```json
{ "type": "error", "error": "Error message" }
```

## Event Sequence

### Math tool flow

```
tool-start → tool-end → tool-result → text-delta* → finish
```

### Search tool flow (unchanged)

```
tool-start → tool-end → sources → tool-result → text-delta* → finish
```

### No-tool flow (unchanged)

```
text-delta* → finish
```
