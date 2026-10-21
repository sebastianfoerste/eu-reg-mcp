# Design teardown (October 2026)

Eight products torn down against the checklist in the research prompt, then compared per checklist item. Sources and evidence tags as in the [landscape](2026-10-competitive-landscape.md); all accessed 2026-10-20. Nothing here is copied: tool and parameter names are cited, behaviour is paraphrased.

## 1. Ansvar (Gateway and archived servers) — Observed source, Claimed gateway

- **Framing.** Disclaimers sit in the README and in a `_meta.disclaimer` on `check_data_freshness` (`src/tools/check-data-freshness.ts`). Dates are available through a separate tool, not on each answer.
- **Tool surface.** 14 snake_case tools in `comprehensive-eu-law-mcp`, verb-first (`search_eu_law`, `get_article`, `validate_citation`, `check_data_freshness`, `about`). No annotations or titles in the registry code.
- **Responses.** JSON text only. A `buildCitation` helper (`src/citation.ts`) attaches `canonical_ref`, `display_text`, `aliases`, `source_url` and a `lookup` naming the tool and arguments that re-fetch the cited item: a re-verification handle.
- **Errors.** Every thrown error becomes `isError: true` with `Error: <message>` (`src/index.ts`); no codes.
- **Citation UX.** `validate_citation` parses `Article 5(1) GDPR` or a case number with regular expressions and reports `valid`, `parsed`, `match` and `warnings`. Issues #35, #71 and #80 show `source_url` and effective dates coming back empty: schema fields without data.
- **Onboarding.** One-line `claude mcp add --transport http` to the gateway; first request opens OAuth. Self-hosting requires re-ingesting because the database is not redistributed (TDM licensing).
- **Adopt:** a re-verification handle per result (we already have `entry_id`; a resource URI makes it fetchable), an `about` surface. **Reject:** hosted-only data, provenance fields that may be empty.

## 2. Lex (i.AI) — Observed source

- **Framing.** README states experimental, not a production dependency.
- **Tool surface.** MCP is generated from FastAPI routes (`FastMCP.from_fastapi`), so tool names are route `operation_id`s (`search_amendments`, `lookup_legislation`, `get_legislation_sections`). Search and lookup are split per collection.
- **Responses.** Pydantic `response_model`s give typed output for free.
- **Change tracking.** Amendments are a first-class searchable collection rather than a diff.
- **Errors.** A `handle_errors` decorator wraps routes; complaint themes are timeouts and unclear filter types (#15, #17).
- **Telemetry.** A PostHog client sits in the backend (`core/posthog_client.py`).
- **Adopt:** typed models as the single source of the output schema; change records as queryable data with filters. **Reject:** analytics in a legal tool (rule 7).

## 3. mcp-server-legifrance — Observed source

- **Framing.** One prompt, `agent_juridique_expert`, instructs the model to cite official links in the body text.
- **Tool surface.** Three French verb-first search tools.
- **Errors.** API errors and exceptions return as ordinary text content without `isError` (`src/server.py`, `call_tool`), so a client cannot tell failure from an answer.
- **Adopt:** a prompt that encodes the citation duty (ours: snapshot date and review framing). **Reject:** errors that look like results.

## 4. cyanheads eur-lex-mcp-server — Observed README and registry record

- **Tool surface.** 7 tools with a common `eurlex_` prefix; 2 resource templates (`eurlex://document/{celexNumber}`, `…/relations`) that mirror tool data; 1 prompt.
- **Responses.** Empty results return an empty page plus a `notice` on how to broaden; `limit_clamp` reports when a limit was reduced; `empty_relation_types` separates "none" from "paged out".
- **Errors.** Per-tool typed codes (`not_found`, `invalid_date_range`, `offset_past_window`, `sparql_timeout`, `content_challenge`).
- **Citation UX.** Resolves CELEX, ELI, ECLI and OJ citations to a CELLAR work; flags superseded consolidations.
- **Adopt:** stable error codes, resource templates that duplicate tool data, explicit notices for empty results. **Differ:** our domain is a register, not legislation; we keep one code set across tools.

## 5. ToolOracle MiCAOracle — Observed README, via [L]

- **Framing.** Results are traffic lights and a "readiness score"; approving a remediation flips a token to green.
- **Freshness.** `freshness_check` downgrades stale evidence, a good idea in itself.
- **Deployment.** Remote-only via `mcp-remote`; daily call quotas.
- **Reject:** entity or token compliance scores (rule 2), hosted-only lock-in. **Adopt (already present):** staleness that changes the answer's framing.

## 6. mcp-eu-sparql — Observed README

- **Responses.** Every result carries `structuredContent.citations` with title, url, CELEX, ECLI, date and a `license` flag for non-commercial sources.
- **Conformance.** An offline drift check keeps the server instructions consistent with the tool list and the error-code enum.
- **Adopt:** a test that the documented error codes equal the implemented ones (our eval suite does this). **Parked:** citation URLs (D2) until EUR-Lex can be verified.

## 7. GitHub MCP Server — Observed README and issues

- **Tool surface.** Toolsets that bundle tools, resources and prompts; a read-only mode; dynamic toolsets.
- **Complaints.** Context bloat from tool lists and large responses (#1286, #957, #2383), paging requests (#567, #1297).
- **Adopt:** keep `tools/list` small; page large lists. **Not needed yet:** toolsets for 5 tools.

## 8. Cloudflare MCP — Observed README

- **Responses.** Each tool result is capped near 6,000 tokens by default; JSON stays valid, cut lists keep whole items, every cut is marked; an opt-out parameter exists.
- **Adopt:** never truncate silently. Our search already pages (25 per page with `truncated`), and change records page by `limit`. Lint (19 KB) and classify (41 KB) are sibling output we must not rewrite (rule 6), so truncation there is parked as an owner decision.

## Sibling overlap: eu-ai-act-classifier's own MCP server

The classifier ships its own MCP tools (`classify_ai_system`, `classify_ai_system_text`, per [C] design-teardown "CLI and MCP developer experience"). eu-reg-mcp's `classify_eu_ai_act_system` wraps `local_api.classify_payload` and adds the `available`/`notice` envelope. Overlap is deliberate (one server for register plus checks), but two MCP surfaces for one engine can drift. Merging is an owner decision; recorded under **Needs owner decision** in the plan.

## Per-checklist comparison

| Checklist item | Best observed pattern | eu-reg-mcp today | Gap |
| --- | --- | --- | --- |
| Framing | Disclaimer in each result (Ansvar `_meta`, ours `notice`) | `notice` on register and lint/classify successes; missing on errors and hints | Errors need `notice` |
| Dates cited | Freshness on each answer (ours), freshness tool (Ansvar) | On search and summary; **missing on changes** | P0 |
| Naming | One prefix per server (cyanheads `eurlex_`) | Mixed verb-first and noun-first | Renaming is breaking → owner decision |
| Titles, annotations | Annotations common; titles rare | Annotations yes; titles no | Add `title` (H1/D1) |
| `tools/list` cost | Cloudflare 2 tools ≈1k tokens | 3,425 B ≈ 856 tokens | Keep ≤ baseline after adding params |
| Typed output | Lex (Pydantic models), mcp-eu-sparql | Permissive object schema | H1 |
| Paging and truncation | Cloudflare marked cuts; cyanheads `limit_clamp` | `offset` + `truncated` on search; `limit` silently clamped to 200 on changes | Add `next_offset`; report clamp |
| Errors | cyanheads typed codes | Mixed: plain-text `isError`, Pydantic text, success dicts with `error` | H1 one error model |
| Empty results | cyanheads `notice` on how to broaden | `total_matches: 0` only | `similar_names` (H3) |
| Resources and prompts | cyanheads templates; Légifrance prompt | none | H2 |
| Citation UX | cyanheads CELEX/ELI resolution; mcp-eu-sparql URLs | Plain strings from siblings | D2 parked (EUR-Lex unreachable) |
| CLI parity | — | `search` lacks `--offset`; `--register` unchecked; limit default 20 vs 50 | P0 / H1 |
| Onboarding | Context7 30+ clients; Lexbeam connector directory | 2 clients in the README; in the MCP Registry at 0.1.1 (an earlier version of this table said it was not listed; corrected 2026-10-21) | D3 built for 6 clients; H6 spec |
| Evals | Sentry evals beside unit tests; mcp-eu-sparql drift check | none | H5 |
| MCP Apps | none of the eight | none | D5 parked |
