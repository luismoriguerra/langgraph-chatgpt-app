# Research: Web Search Tool for AI Chat

**Branch**: `002-web-search-tool` | **Date**: 2026-04-07

## 1. LangGraph ReAct Agent Pattern

**Decision**: Use `create_react_agent` from `langgraph.prebuilt` to build the agent graph.

**Rationale**: The project already declares `langgraph>=0.2.0` as a dependency but does not use it. The existing `chat_graph.py` is a stub with `ChatState` and `TitleState` TypedDicts but no compiled graph. `create_react_agent` provides a production-ready ReAct loop (reason → act → observe → repeat) that handles tool binding, conditional branching, and stopping conditions out of the box. This avoids hand-rolling a custom `StateGraph` for a well-understood pattern.

**Alternatives considered**:
- **Custom `StateGraph`**: More control but unnecessary complexity for a single-tool agent. Violates Principle VII (Simplicity).
- **LangChain AgentExecutor (legacy)**: Deprecated in favor of LangGraph agents. Not recommended.

## 2. DuckDuckGo Search Tool

**Decision**: Use `DuckDuckGoSearchResults` from `langchain-community` with `duckduckgo-search` as the underlying library.

**Rationale**: Free, no API key required, returns structured results (title, snippet, link). Aligns with the assumption in the spec that no paid subscriptions are needed. The `langchain-community` integration provides a `BaseTool` interface compatible with `bind_tools`.

**Configuration**:
- `num_results`: 4 per search call (balances quality vs. token cost)
- `source`: `"text"` (no image/video per spec assumption)
- Max 3 tool calls per turn (per spec FR-002)

**Alternatives considered**:
- **Tavily Search**: Better quality results but requires a paid API key. Rejected for v1 simplicity.
- **SerpAPI**: Paid, requires API key. Rejected.
- **Brave Search API**: Free tier available but requires API key registration. Rejected for zero-config goal.

## 3. Streaming Strategy

**Decision**: Use `astream_events(version="v2")` from the compiled LangGraph agent to stream tokens and tool events.

**Rationale**: `astream_events` provides granular event filtering — we can listen for `on_chat_model_stream` events for token-by-token output and `on_tool_start`/`on_tool_end` events for tool usage indicators. The existing SSE protocol (`text-delta`, `finish`) will be extended with `tool-start` and `tool-end` event types.

**Known issue**: `astream()` with `stream_mode="messages"` has compatibility issues with `create_react_agent` in recent LangGraph versions. `astream_events` is the recommended approach.

**Alternatives considered**:
- **`astream()` with `stream_mode="values"`**: Only emits full state after each node completes. No token-level streaming. Rejected.
- **`astream_log()`**: Too verbose for production SSE. Rejected.

## 4. Tool Invocation Persistence

**Decision**: Add a `tool_invocations` table with a FK to `messages`, storing tool name, input, output, and timestamp. Use a JSON column for structured output (result snippets + source URLs).

**Rationale**: Per clarification, tool invocations must persist for source link survival across reloads. A separate table (vs. JSON column on messages) allows querying tool usage independently and avoids bloating the messages table.

**Alternatives considered**:
- **JSON column on `messages` table**: Simpler schema but mixes concerns. Rejected — harder to query and index.
- **Ephemeral (no persistence)**: Rejected per clarification decision.

## 5. SSE Protocol Extension

**Decision**: Extend the existing SSE event stream with two new event types.

| Event Type | Payload | When |
|------------|---------|------|
| `text-delta` | `{ textDelta: string }` | Each streamed token (existing) |
| `tool-start` | `{ toolName: string, toolInput: string }` | Agent decides to call a tool |
| `tool-end` | `{ toolName: string }` | Tool execution completes |
| `sources` | `{ sources: [{ title, url, snippet }] }` | After all tool calls, before final answer begins |
| `finish` | `{ finishReason: string }` | Stream ends (existing) |

**Rationale**: Backward compatible — existing frontend already ignores unknown event types (try/catch in the SSE parser). New events enable the UI search indicator (FR-005) and source citation display (FR-003).

## 6. New Dependency: `langchain-community` + `duckduckgo-search`

**Decision**: Add `langchain-community>=0.3.0` and `duckduckgo-search>=6.0.0` to `pyproject.toml` dependencies.

**Rationale**: `langchain-community` provides `DuckDuckGoSearchResults` tool. `duckduckgo-search` is its required backend. Both are well-maintained and actively used. This is justified per Principle VII — it solves a concrete, present problem (web search capability).
