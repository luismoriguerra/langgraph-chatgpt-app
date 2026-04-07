# Data Model: Math Solver AI Tool

**Branch**: `003-math-tool` | **Date**: 2026-04-07

## Entity Changes

### ToolInvocation (modified)

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| id | UUID | existing | Primary key |
| message_id | UUID (FK) | existing | References messages.id |
| tool_name | String(50) | existing | Tool identifier (e.g., `web_search`, `calculate`) |
| tool_input | Text | existing | Raw input passed to the tool |
| tool_output | JSON | existing | Structured output for search-type tools (list of SearchResult dicts) |
| **tool_result** | **Text, nullable** | **NEW** | **Raw string output from any tool (e.g., `"1024"` for math, raw JSON for search). Nullable for backward compatibility with existing rows.** |
| created_at | DateTime | existing | Timestamp |

### Database Migration

**Migration**: `add_tool_result_column`

```sql
ALTER TABLE tool_invocations ADD COLUMN tool_result TEXT;
```

Downgrade:

```sql
ALTER TABLE tool_invocations DROP COLUMN tool_result;
```

No data backfill needed. Existing `web_search` invocations will have `tool_result = NULL`, which is acceptable since their data is already in `tool_output`.

## Entity Relationships (unchanged)

```
Conversation 1 ──── * Message 1 ──── * ToolInvocation
```

No new entities, tables, or relationships introduced.
