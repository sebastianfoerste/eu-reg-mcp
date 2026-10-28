# 0010. MCP Apps register view

- **Status:** Proposed; owner decision.
- **Date:** 2026-10-20

## Context

None of the eight torn-down products ships an MCP Apps view. mcp 1.28.1 can register a resource at any URI and attach `meta` to tools, so a `ui://` resource is technically servable on 1.x; client support was not verified (client docs unreachable).

## Decision (proposed)

- One self-contained HTML resource (`ui://micar/search`), no CDN, CSP with no external origins, system fonts, tabular numerals, one column at 375 px, dark mode, a table before any chart; the snapshot date and `notice` always visible; no scores beyond the string-match basis.

## Consequences

- A UI is a product decision and a maintenance cost; parked with the 2.x port.
