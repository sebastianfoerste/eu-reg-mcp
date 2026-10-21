# Adaptation plan (October 2026)

Inputs: [landscape](2026-10-competitive-landscape.md) · [feature matrix](feature-matrix.csv) · [design teardown](design-teardown.md). ADRs: [`docs/adr/`](../adr/). Evidence tags as defined in the landscape; sources accessed 2026-10-20. **[L]** and **[C]** cite the linter and classifier research on branch `feat/competitive-adaptation-2026-10` of those repositories.

## 1. Baseline and results

| Measure | Baseline (`68303d6`) | After this branch | How measured |
| --- | --- | --- | --- |
| Tests | 39 passed | 125 passed (incl. 25 eval tasks, 7 ranking checks) | `uv run pytest -q` |
| `tools/list`, whole (compact JSON) | 3,425 B (~856 tokens) | 7,478 B (~1,870 tokens) | scratch stdio client |
| `tools/list` without `outputSchema` (names, titles, descriptions, inputs) | 2,904 B | 2,904 B, with 7 more parameters and 5 titles | `test_tools_list_input_side_stays_within_budget` |
| Field-level `outputSchema` | 0 of 5 tools | 5 of 5 | contract tests |
| Resources / templates / prompts | 0 / 0 / 0 | 3 / 1 / 2 | `resources/list`, `prompts/list` |
| Error shapes | 4 (plain-text `isError`, Pydantic text, `{"available": false}`, `{"error": "…"}`) | 1 (`code`, `error`, `hint`, `notice`; 5 codes) | stdio transcript |
| Register answers with `snapshot_date`, `stale` | 2 of 3 tools | 3 of 3 tools, 3 of 3 register resources, all register errors (as `null`) | evals |
| Search real-match hit@1 / hit@5 (22 fictional queries; `results` only) | 0.18 / 0.36 | 0.36 / 0.36 (8 of 8 queries with a literal match now rank it first, was 4 of 8) | `tests/evals/test_ranking.py` |
| `similar_names` recall@1 on the 14 zero-match queries (not matches) | none offered | 1.00 | same |
| Response bytes: search / summary / changes | 1,739 / 1,737 / 2,292 | 2,011 / 1,772 / 2,827 | `CallToolResult`, fixtures |
| Response bytes: lint / classify | 19,165 / 41,038 | 19,165 / 41,038 (unchanged: sibling output passes through) | same |
| Wheel | 13,979 B | 22,409 B | `uv build` |
| `serverInfo.version` | `1.28.1` (the SDK's) | the package version | handshake |
| Declared `mcp` floor | `>=1.9` (1.10 and 1.12 fail 38 of these tests; ≤1.20 do not install beside current pydantic) | `>=1.22` (full suite passes on 1.22.0, 1.24.0, 1.26.0, 1.28.1) | `uv run --isolated --with mcp==X pytest` |
| README words | 890 | 882 | `wc -w` |

Until the 2026-10-21 audit these were reported as one figure (hit@1 0.18 → 1.00) that counted `similar_names` as hits; they are not matches (rule 2), so the two are now measured apart. Misspellings and legal-form variants (for example "Example Issuer AG" for "Example Issuer GmbH") still return zero matches by design: a different legal form may be a different entity, so they surface only as `similar_names`. The benchmark was written alongside the algorithm, so even these figures overstate real-world precision. A live sanity check (not committed) showed no `similar_names` for nonsense queries.

## 2. Best-of candidates

Impact 1–5 on the lawyer's, drafter's or assessor's job; Fit names the rule; Effort S/M/L; Evidence is the weakest tag behind the idea; T = table stakes, D = differentiator.

| # | Candidate | Inspiration | Impact | Fit | Effort | Evidence | T/D | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | Date changes; CLI `--offset`; fictional fixtures; doc fixes | own gaps | 5 | pass (rules 1, 5) | S | Observed | T | **Built** |
| H1 | Typed output + one error model | Lex (Pydantic models), cyanheads (typed codes), Ansvar (`isError`) | 5 | pass (rules 1, 3) | M | Observed | T | **Built** |
| H3 | Explained ranking, `similar_names`, change filters | yente (score + basis), cyanheads (notice on empty), Lex (amendments as data) | 4 | pass (rule 2: string similarity only) | M | Observed | D | **Built**; `as_of` parked |
| H2 | Resources, entry template, prompts | cyanheads templates, Légifrance prompt, Ansvar `about` | 4 | pass (rules 1, 3) | M | Observed | T | **Built** |
| H5 | Contract eval suite | Sentry (evals beside tests), mcp-eu-sparql (drift check) | 4 | pass (rule 6: no model) | M | Observed | D | **Built** |
| H6 | Ship the unreleased items | MCP Registry, PyPI | 5 | pass if owner publishes | S | Observed | T | Version source and agreement test **built**; `release.yml` **spec** |
| D1 | Titles and sharper descriptions within budget | GitHub/Cloudflare context complaints | 3 | pass | S | Observed | T | **Built** (with H1/H3) |
| D3 | `docs/clients.md` for 6+ clients | Context7 (30+ clients, Claimed), Lex | 3 | pass | S | Observed | T | **Built** on 2026-10-21 for 6 clients whose official docs were readable (see §3) |
| H4 | Full linter/classifier options, document input | linter CLI, classifier `local_api` | 4 | pass with ADR | L | Observed | D | **Spec** ([ADR 0006](../adr/0006-document-input-for-lint.md)) |
| D2 | `citation_links` (CELEX/ELI) | cyanheads, mcp-eu-sparql, Ansvar | 4 | **fail today**: EUR-Lex unreachable, links unverifiable | M | Claimed | D | **Parked** ([ADR 0008](../adr/0008-citation-links.md)) |
| H7 | Docker and authenticated remote HTTP | Exa, GitHub, cyanheads | 3 | owner decision (rule 8) | M | Observed | T | **ADR only** ([0007](../adr/0007-docker-and-authenticated-http.md)) |
| H8 | GLEIF LEI enrichment | WhitePaperXBRL via [L], MiCA CASP Tracker | 3 | **park**: API unreachable, rate limit unverified (rule 7) | M | Claimed | D | **Parked** |
| D4 | Optional guardrail skill | Ansvar plugin (Claimed) | 2 | pass | S | Claimed | D | **Spec** (prompts cover most of it) |
| D5 | MCP Apps register view | none of the eight | 2 | owner decision | M | Inferred | D | **Parked** ([0010](../adr/0010-mcp-apps-view.md)) |
| — | Readiness traffic lights, entity scores | ToolOracle MiCAOracle | — | **fail** rule 2 | — | Observed | — | **Rejected** |
| — | Hosted-only OAuth gateway | Ansvar Gateway | — | fail rules 7, 8 as a default | — | Claimed | — | **Rejected** as default; see H7 |
| — | Tool toolsets / `?tools=` selection | GitHub, Exa | 2 | pass | S | Observed | T | **Not needed** at 5 tools |
| — | Default response truncation | Cloudflare | 3 | **fail** rule 6 for sibling output | M | Observed | T | **Owner decision** (lint 19 KB, classify 41 KB) |

## 3. Hypotheses and design upgrades: verdicts

| Item | Verdict | Evidence |
| --- | --- | --- |
| H1 Typed output, one error model | **Confirmed, modified.** Field-level schemas cost 4,576 B in `tools/list`; input-side bytes held at baseline. Errors are `isError` results whose `structuredContent` the Python client does not validate against `outputSchema` (`ClientSession.call_tool` skips validation when `isError`; Observed in mcp 1.28.1). | [ADR 0001](../adr/0001-typed-output-and-error-model.md) |
| H2 Resources, templates, prompts | **Confirmed.** No rule-catalogue resource: the linter exports none ([L] plan lists it as a follow-up). | [ADR 0003](../adr/0003-resources-and-prompts.md) |
| H3 Ranking, filters, `as_of` | **Modified.** Ranking and filters built; `as_of` **parked**: the observatory has 16 dated snapshots but no index and an irregular date (2026-07-13), so a client would have to probe dates blind. An exact-LEI filter on changes is **built** (added after the 2026-10-21 audit: the research wrongly said changelog records carry no LEI; records from the 2026-10-19 snapshot on carry `lei`, older ones do not, so `entry_id` remains the filter for those). | [ADR 0002](../adr/0002-deterministic-search-ranking.md), [0005](../adr/0005-point-in-time-as-of.md) |
| H4 Full linter/classifier options | **Parked as spec.** The lock is now on 0.2.1 (2026-10-21); still needs a `python-docx` extra and a file-input ADR. | [ADR 0006](../adr/0006-document-input-for-lint.md) |
| H5 Contract evals | **Confirmed.** 25 tasks (21 at first, 4 added after the audit); found one real inconsistency (register `invalid_input` without null provenance), fixed. Model-driven evals stay spec. | [ADR 0004](../adr/0004-contract-evals.md) |
| H6 Ship Unreleased | **Confirmed, partly built.** `__version__`, `User-Agent`, `serverInfo.version`, agreement test and a proposed `0.2.0 (unreleased)` heading. Publishing is an owner action: 0.2.0 goes to PyPI and, as a new version, to the existing MCP Registry entry (0.1.0 and 0.1.1 are listed since 2026-10-15; the first version of this plan wrongly said the server was not listed). | [ADR 0009](../adr/0009-release-workflow.md) |
| H7 Docker, authenticated HTTP | **ADR only, owner decision.** | [ADR 0007](../adr/0007-docker-and-authenticated-http.md) |
| H8 GLEIF | **Parked.** api.gleif.org unreachable; CC0 licence and throttling seen only in snippets (Claimed). Precedent found 2026-10-21: cz-agents eu-registry queries GLEIF without auth and caches responses in SQLite for 7 days by default (README, Observed). | landscape §4, §6 |
| D1 Descriptions and titles | **Confirmed.** 5 titles; descriptions tightened; input-side bytes 2,904 = baseline. | budget test |
| D2 `citation_links` | **Parked.** EUR-Lex and CELLAR unreachable; CELEX `32023R1114` and ELI `reg/2023/1114/oj` seen only in snippets. Unverifiable means no link. | [ADR 0008](../adr/0008-citation-links.md) |
| D3 `docs/clients.md` | **Built (2026-10-21).** Parking it was a mistake: official docs for Zed, Gemini CLI, Continue and goose are readable on GitHub. `docs/clients.md` covers those plus Claude Code and Claude Desktop, with source URLs and read dates; the two `uvx` command/args pairs were tested with a scratch stdio client against PyPI 0.1.1. VS Code, Cursor, Cline and Codex are listed as not reachable. | [docs/clients.md](../clients.md) |
| D4 Guardrail skill | **Modified.** The two prompts now carry the guardrails inside MCP itself; a separate skill is low value until clients surface prompts poorly. Spec only. | — |
| D5 MCP Apps | **Parked.** 1.28.1 could serve a `ui://` resource and tool `_meta`, so the SDK is not the blocker; a UI is a product decision. | [ADR 0010](../adr/0010-mcp-apps-view.md) |

Research questions, briefly: (1) 1.28.1 negotiates `2025-11-25`; stateless requests, per-request log level and JSON Schema 2020-12 everywhere need the 2.x SDK (2026-07-28 spec). Which primitives each client surfaces could not be verified (client docs unreachable). (2) Typed models add field-level validation and a contract for the evals at +4.6 KB of `outputSchema`; the JSON text block keeps text-only clients working. (3) `isError` results with a five-code set; protocol errors only for resources. (4) Search plus `micar://entry/{entry_id}` is our resolve-then-fetch pair; responses page at 25 results / ≤200 changes. (5) Tiered string matching plus `difflib` after legal-form stripping, no new dependency. (6) Needs an observatory index (sibling follow-up). (7) See ADR 0008. (8) See ADR 0006. (9) PyPI Trusted Publishing and `mcp-publisher` need owner setup; spec in ADR 0009. (10) See ADR 0007. Today `--host 0.0.0.0` binds all interfaces, but FastMCP fixes its localhost-only Host and Origin allow-list when the server object is built (`mcp/server/fastmcp/server.py` lines 178–182 in 1.28.1, Observed), and `main()` changes only `settings.host` afterwards, so requests with a non-local Host header are refused.

## 4. Specs of what was built

### P0 — register changes dated, small defects (commit `9025a7f`)
- **Story.** A lawyer asking "what was removed?" gets the snapshot date with the answer.
- **Built.** `micar_register_changes` returns `snapshot_date`, `data_age_days`, `stale`, `observatory_snapshot`; CLI `search --offset`; `offset` documented; duplicate README sentence removed; fixture row copied from the live register replaced with fictional `Sample Ledger Labs GmbH` / `529900EXAMPLELEI0002`, and the removal record with `Former Example Token AG` (id `a3`, not in the snapshot, so `still_listed` is false as it would be live); a fixture guard test.
- **Acceptance.** Met: tests `test_changes_tool_states_snapshot_provenance`, `test_cli_search_offset`, `test_fixtures_use_no_live_register_rows`.

### H1 — typed output and one error model (commit `a4c4eb9`)
- **Story.** An agent can tell a failed lookup from an empty one, and recover.
- **References.** Lex `response_model` routes; cyanheads typed codes; Ansvar `isError` text; Légifrance errors-as-text (anti-pattern).
- **Adapted.** Pydantic response models per tool; schemas compacted (no generated titles, `X | None` folded to a type list). A `FastMCP` subclass maps a raised `ToolFailure`, and argument `ValidationError`s, to `isError` results with the same JSON in text and `structuredContent`. Cached-fallback answers carry `warnings`. Linter timeouts and non-JSON output are caught.
- **Different.** One code set for all tools rather than per-tool codes; the `notice` stays on errors; legacy keys (`available`, `hint`, `error`) kept.
- **Behaviour change.** A missing extra or invalid JSON now sets `isError: true` (was an ordinary result). Listed under owner decisions for release notes.
- **Dependency floor.** Tool titles and typed output need a newer SDK than the declared `mcp>=1.9`; the floor is now `mcp>=1.22,<2`, the oldest release the suite was run on and passed.
- **Tests.** `tests/test_mcp_contract.py` (schema validation over the wire, every code, CLI exit codes).

### H3 — ranking, similar names, change filters (commit `aeaa47f`)
- **Story.** A drafter who types "Orbit" or misspells a name finds the right entry first, and is told plainly when nothing matched.
- **References.** yente `score`, `match` and per-feature explanations (`yente/scoring.py`, `yente/data/common.py`); cyanheads `notice` on empty results; Lex amendments search.
- **Adapted.** Same match set as before (substring or exact LEI), ordered by tiers with `match.score` and `match.basis`; equal scores keep register order so paging is stable. With zero matches, ≤5 `similar_names` (`difflib` ratio ≥0.8 against the whole name or a same-length word run, after dropping trailing legal forms), each labelled `"not a match"`; none for LEI-shaped queries. Changes filter by `since`, `until`, `register_slug`, `member_state`, `entity`, `entry_id` and exact `lei` (records from 2026-10-19 on), accept the provisional `missing` change type, and page with `offset`/`next_offset`.
- **Different.** No fuzzy widening of the match set: a register answer never includes an entity the query did not literally match. Scores describe the string, never the entity.
- **Tests.** `tests/evals/test_ranking.py`, `test_change_filters`, contract tests.

### H2 — resources, template, prompts (commit `8db039c`)
- **Story.** A client can pin "the entry I am talking about" by URI and reuse a vetted prompt.
- **References.** cyanheads `eurlex://document/{celexNumber}`; Légifrance `agent_juridique_expert`; Ansvar `about`, `check_data_freshness`.
- **Built.** `eu-reg://about`, `micar://summary`, `micar://changes`, `micar://entry/{entry_id}`; prompts `check_register_status(entity)` and `review_register_changes(since)`. Single-source `__version__` feeds `User-Agent` and `serverInfo.version`.
- **Tests.** `tests/test_resources_prompts.py`.

### H5 — contract evals (commit `e1896bc`)
- **Story.** The maintainer can change wording or code and know the contract still holds.
- **Built.** 25 JSON tasks plus runner (every error code including `upstream_failed`, the `missing` change type and the LEI filter); checks dates, notice placement, error codes, schema validity, unchanged sibling output (byte-equal to a direct `micar-lint --json` and `classify_payload` call), and no `compliance_status`/`risk_score`-style keys. A release-metadata test (versions, `mcp-name`, newest CHANGELOG heading).
- **Spec only.** Model-driven evals (Sentry-style: a model answers "is X on the register?" and a grader checks the date and notice) need a key and network; not in CI.

## 5. Specs not built

### H6 `release.yml` (spec; owner action to enable)
```yaml
on:
  release:
    types: [published]
permissions:
  contents: read
jobs:
  build:      # uv build; upload dist/ as an artifact; no secrets
  pypi:       # environment: pypi (required reviewers); permissions: id-token: write
              # uses the PyPI Trusted Publisher; action pinned by SHA
  registry:   # environment: mcp-registry (required reviewers); id-token: write
              # mcp-publisher login github-oidc && mcp-publisher publish
```
No `secrets.*`; `id-token: write` only inside the two environments. Owner steps: create the Trusted Publisher on PyPI, the two environments with reviewers, then cut release 0.2.0 (bump `pyproject.toml` and both `server.json` versions together; the agreement test enforces it). This branch adds **no** workflow.

### H4 full linter and classifier options (spec)
Expose `type`, `lang`, `strict`; return remediation, coverage and review-table JSON by running `micar-lint` with `--remediation-output` etc. into a temp dir; accept Markdown/XHTML text as a string and PDF/DOCX as base64 blobs (stdio and HTTP alike; never a server-side path over HTTP); add `python-docx` to the `lint` extra. Expose classifier `sources_payload`, `artifacts_payload`, `dossier_payload` and a schema-level `include_advisory`. The lock is already on 0.2.1. See ADR 0006.

### D3 client docs (built 2026-10-21)
See [docs/clients.md](../clients.md). Still to add once their official pages can be read: VS Code, Cursor, Cline, Codex.

### D4 guardrail skill (spec)
An optional `SKILL.md` restating the prompts' rules for clients without prompt support. Wording is legal-effect: maintainer review first.

### H8 GLEIF (parked)
Opt-in `--enable-gleif` flag, `openWorldHint=True`, cached per LEI, mocked in tests, documented in `SECURITY.md`; returns GLEIF's legal name and status beside, never inside, register facts. Blocked until api.gleif.org terms and rate limits can be read. Precedent: cz-agents eu-registry (MIT) calls GLEIF without auth and caches responses in SQLite with a 7-day default TTL (`GLEIF_CACHE_PATH`, `GLEIF_CACHE_TTL_DAYS`); the same per-LEI disk cache would fit rule 7.

## 6. Anti-patterns tested

| Anti-pattern | Who (evidence) | Rule broken | Our status |
| --- | --- | --- | --- |
| Unlinked shorthand citations | this repo and siblings (`Anhang I Teil A MiCAR`); Légifrance relies on the model to add links | verifiable citations | Still present; D2 parked until EUR-Lex is reachable |
| Undated answers | Ansvar (date via separate tool); this repo's changes tool before P0 | rule 1 | Fixed: every register answer and error |
| Silent truncation | this repo: `limit` silently clamped to 200 | — | `next_offset` added; clamp documented; sibling outputs not truncated (owner decision) |
| Bloated tool lists | github-mcp-server #1286, #957 | context cost | Input side held at baseline; budget test |
| Inconsistent errors | Légifrance (errors as text), this repo's four shapes | rule 3 | One shape, five codes |
| Entity compliance scores | ToolOracle MiCAOracle traffic lights and readiness score | rule 2 | Rejected; eval forbids such keys |
| Guessed removal reasons | none observed; prompt guards it | rule 3 | Prompt and notice say the register does not state why |
| LLM summaries in the checking path | mica-crypto-mcp has no logic at all ([L]); none observed doing LLM checks | rule 6 | Evals assert sibling output passes through unchanged |
| Unauthenticated remotes | Lexbeam hosted (no auth, by design, stateless); this repo's HTTP transport | rule 8 | Localhost default kept; H7 ADR |
| Hosted-only lock-in | Ansvar Gateway (DB not redistributed), ToolOracle | rule 7 | Rejected; data stays public on GitHub |
| Default-on telemetry | Lex backend PostHog client; legalithm and ArkForge per [C] | rule 7 | None here |
| Empty provenance fields | Ansvar #35, #71, #80 | rule 2 | Evals require dates and source URLs to be present |

## 7. Positioning

Hypothesis: *the only free, open MCP server whose MiCAR answers are dated and traceable to the ESMA file and entry, with deterministic, review-gated checks and verified EUR-Lex links.* **Modified.** For the MiCAR register, no other MCP server was found: the registry search for "mica" returned a stub (mica-crypto-mcp) and a hosted checker (micarequirements.com), and the CASP trackers are web directories without an MCP surface (Claimed). Lexbeam and cyanheads show that free, open, dated and deterministic are not unique in adjacent domains, and the "verified EUR-Lex links" part is **not true yet** (D2 parked). Supported claim: *eu-reg-mcp is the only open MCP server found that answers from the ESMA interim MiCAR register, and every answer carries the snapshot date, the ESMA source file and the entry id, with typed errors and deterministic, review-gated white paper and AI Act checks.*

## 8. Attempted, reverted

None.

## 9. Needs maintainer legal review

New or changed wording that describes legal effect or frames outputs (`NOTICE`, `REVIEW_NOTICE` and the server `instructions` are unchanged):

Line numbers as of the audit follow-up commit (2026-10-21):

- `src/eu_reg_mcp/server.py:134–222` — tool titles and the rewritten tool descriptions (search, summary, changes, lint, classify), including the changes description's "missing: provisional, not a removal" (line 184).
- `src/eu_reg_mcp/server.py:49, 66, 73, 114–117` — error messages and hints (`Unexpected …`, `See the tool's inputSchema…`, the `data_unavailable` hint).
- `src/eu_reg_mcp/server.py:238` — resource error messages now end with `Notice: ` and the register `NOTICE`.
- `src/eu_reg_mcp/server.py:250–308` — resource titles and descriptions; `:314–316` unknown-entry message ("may have been removed … or never existed").
- `src/eu_reg_mcp/server.py:321–335` — prompt `check_register_status` (title, description, text; includes "do not assess whether the entity is authorised, compliant or trustworthy").
- `src/eu_reg_mcp/server.py:339–356` — prompt `review_register_changes` (title, description, text), including the new sentence that a `missing` record is provisional and must not be reported as a removal.
- `src/eu_reg_mcp/integrations.py:92, 102, 131–132, 144, 174–175` — error messages and hints for lint and classify.
- `src/eu_reg_mcp/data.py:186–188` — the cached-fallback warning.
- `src/eu_reg_mcp/register.py:223` and `src/eu_reg_mcp/models.py:81–82, 120` — `"not a match"` label and the `match.score` / `similar_names` schema descriptions.
- `docs/guardrails.md:8` — paragraph on prompts and scores.
- `docs/tools.md` — the changes paragraph defining `missing` as provisional (line 15), the search ranking paragraph (line 13), "Typed output and errors" and "Resources and prompts" sections.
- `docs/clients.md` — client setup instructions (operational, listed for completeness).
- `README.md` — example output note, example (fictional entity) and the sentence that `match` says nothing about the entity.

## 10. Needs owner decision

1. **Publish 0.2.0** (CHANGELOG heading proposed) to PyPI and as a new version of the existing MCP Registry entry (0.1.0 and 0.1.1 are listed, both published 2026-10-15); optionally move both to CI with Trusted Publishing per §5. `uvx eu-reg-mcp` still runs 0.1.1.
2. **Behaviour change in 0.2.0**: missing extras and invalid JSON now return `isError: true`; register order of search results is now ranked.
3. ~~**Lock bump** to micar-whitepaper-linter 0.2.1 and eu-ai-act-classifier 0.2.1~~: done on 2026-10-21 at the owner's request, with the `lint`/`classify` extras floors raised to `>=0.2.1`; lint and classify output on the eval inputs is unchanged. H4 can follow.
4. **Merge or keep** the two MCP surfaces for the classifier (this server's tool and the classifier's own server).
5. **Truncation** of lint (19 KB) and classify (41 KB) responses: a cap would rewrite sibling output (rule 6) unless done as paging the sibling exposes.
6. **Tool renaming** for consistent verb-first names (breaking; would need aliases).
7. **H7** Docker image and authenticated remote HTTP; **D5** MCP Apps view; the **`mcp` 2.x port** (2026-07-28 features).
8. **mcp 1.30.0** is available on 1.x (locked 1.28.1); Dependabot should pick it up.

## 11. Sibling follow-ups (record only; not done here)

- **micar-register-observatory:** publish `data/snapshots/index.json` (dates and file names) so `as_of` can pick the latest snapshot on or before a date without listing the repo. (An earlier version also asked for `lei` on changelog records; they already carry it from the 2026-10-19 snapshot on, so that follow-up was withdrawn.)
- **micar-whitepaper-linter:** a rule-catalogue export (JSON) that this server could expose as a resource; its PR #30 adds `--sarif-output`, `--summary-output` and `--annotations-output`, which a later wrapper could pass through once released.
- **eu-ai-act-classifier:** its PR #31 adds human-readable labels (`catalog.py`) and a guided intake (`intake.py`); once released, the wrapper could expose the intake schema as a resource. Until then eu-reg-mcp keeps working against 0.2.0/0.2.1 from PyPI.
