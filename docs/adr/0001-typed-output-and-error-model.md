# 0001. Typed tool output and one structured error model

- **Status:** Accepted, built on `feat/competitive-adaptation-2026-10`.
- **Date:** 2026-10-20

## Context

With mcp 1.28.1 each `dict[str, Any]` tool already advertised a permissive `outputSchema` (`{"type": "object", "additionalProperties": true}`), so clients could not validate fields. Failures came in four shapes: plain-text `isError` from exceptions, Pydantic validation text, and ordinary results carrying `{"available": false, "hint"}` or `{"error": "…"}`. Lex derives MCP output from Pydantic response models; cyanheads eur-lex-mcp-server returns typed error codes; Légifrance returns errors as ordinary text (see `docs/research/design-teardown.md`).

## Decision

- Each tool is annotated with a Pydantic response model (`src/eu_reg_mcp/models.py`). FastMCP turns it into a field-level `outputSchema` and validates every success. Schemas are compacted: generated `title`s and `null` defaults are dropped and `X | None` becomes a type list. In `inputSchema`, generated parameter titles are dropped too, and so are empty-string defaults (`"default": ""` on search `member_state`; changes `member_state`, `entity`, `entry_id` and `lei`; classify `profile_json`), which only restate that the parameter is optional; `required` already says so. That is how the input side fits its 2,904-byte budget (2,902 bytes after the audit follow-up added `lei` and `missing`).
- Tools raise `ToolFailure(code, message, hint, notice, extra)` (`errors.py`). A small `FastMCP` subclass overrides `call_tool` and returns `CallToolResult(isError=True)` with the error JSON in the text block only, without `structuredContent`. Argument `ValidationError`s map to `invalid_input`; any other exception inside a tool maps to `upstream_failed`, so every failure keeps a code and its notice. Five codes: `data_unavailable`, `extra_missing`, `invalid_input`, `upstream_failed`, `timeout`.
- Errors keep the response's `notice`; register-tool errors carry `snapshot_date`, `data_age_days`, `stale` as `null`. A cached-fallback answer is a success with a `warnings` entry, not an error.
- Existing keys stay (`available`, `hint`, `error` as a string); `notice` stays last.

## Consequences

- `tools/list` grows from 3,425 to 7,478 bytes; the input side (what a model reads to choose a tool) stays at its 2,904-byte baseline, enforced by a test. Whether hosts pass `outputSchema` to the model is unknown (Inferred: likely not to the prompt).
- Error results carry no `structuredContent`. The spec (2025-11-25, tools: structured content) requires `structuredContent` to conform to `outputSchema`, and while the Python client skips validation on `isError`, the TypeScript SDK client (1.x, `Client.callTool`, read 2026-10-21) validates `structuredContent` whenever it is present, even on errors, and throws. The first version of this ADR sent the error body as `structuredContent` and relied on the Python behaviour; a 2026-10-21 audit showed TypeScript-based hosts would have lost the code, hint and notice. A contract test now checks that no error result contradicts its tool's `outputSchema`.
- A missing extra or invalid JSON now sets `isError: true`; release notes must say so.
- The override relies on FastMCP wrapping tool exceptions in `ToolError` with `__cause__`, and the schema compaction sets `Tool.parameters` after registration (`mcp._tool_manager`). Both are 1.x internals; the 2.x port (owner decision) must revisit them.
