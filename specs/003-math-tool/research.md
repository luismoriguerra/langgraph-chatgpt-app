# Research: Math Solver AI Tool

**Branch**: `003-math-tool` | **Date**: 2026-04-07

## R1: Safe math expression evaluation in Python

**Decision**: Use Python `ast.literal_eval` combined with a restricted `compile` + `eval` approach using only the `math` stdlib module.

**Rationale**: The tool needs to evaluate expressions like `sqrt(144) + 3**2` and `(50 + 30) * 2 - 15` safely. `ast.literal_eval` alone cannot handle function calls or operators. A restricted eval that only exposes `math` module functions and no builtins is safe against code injection while supporting all operations required by the spec (FR-001 through FR-003, FR-007).

**Alternatives considered**:
- `numexpr` library: External dependency, overkill for arithmetic. Rejected per Constitution VII (YAGNI).
- `sympy.sympify`: Pulls in the entire SymPy library. Overkill for arithmetic; spec explicitly excludes symbolic algebra.
- Unrestricted `eval()`: Security risk. Rejected.
- `ast.literal_eval` only: Cannot handle operators or math functions. Insufficient.

**Implementation pattern**:
```python
import ast
import math

SAFE_NAMES = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})

def safe_eval(expression: str) -> float | int:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute)):
            raise ValueError(f"Unsafe expression: {expression}")
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, SAFE_NAMES)
```

## R2: Extending tool_output persistence for non-search tools

**Decision**: Add a nullable `tool_result` text column to `tool_invocations` table. Keep existing `tool_output` JSON column for search-specific source data.

**Rationale**: The current `tool_output` column stores `list[SearchResult]` (JSON array of `{title, snippet, url}` dicts). Math tool output is a scalar string like `"1024"`. Rather than breaking the existing search result schema, a new `tool_result` field stores the raw tool output as a string for any tool. This is additive (no breaking changes) and generic (works for future tools too).

**Alternatives considered**:
- Overload `tool_output` with union types: Would require migrating existing data and complicating the domain entity. Rejected.
- Store math result as `[{"snippet": "1024", "title": "", "url": ""}]`: Semantically incorrect. Rejected.
- Separate tables per tool type: Over-engineered. Rejected per Constitution VII.

## R3: Frontend tool result rendering strategy

**Decision**: Create a generic `ToolResultCard` component that renders differently based on `tool_name`. For `web_search`, shows source links. For `calculate`, shows the expression and result. Component is used both during streaming (via SSE events) and on conversation reload (via persisted `tool_invocations`).

**Rationale**: The spec requires tool invocation transparency (FR-005) and persistence on reload (FR-008). A single component handles both live and reloaded states, with tool-name-based rendering for different tool types.

**Alternatives considered**:
- Separate components per tool: Would work but doesn't scale. A single component with internal branching is simpler.
- Extend `SearchIndicator`: Too tightly coupled to search semantics. Better to create a new generic component.

## R4: SSE event extension for tool results

**Decision**: Add a `tool-result` SSE event type emitted after `tool-end` for every tool, carrying `{ toolName, toolInput, result }`. This complements the existing `sources` event (which remains search-specific).

**Rationale**: The frontend needs the raw tool output to display in the tool card. Currently, `on_tool_end` emits `tool-end` + `sources`, but `sources` is empty for non-search tools. A new `tool-result` event provides the raw output generically.

**Alternatives considered**:
- Embed result in `tool-end` event: Would change the existing contract. Rejected to preserve backward compatibility.
- Reuse `sources` event with a different shape: Confusing semantics. Rejected.
