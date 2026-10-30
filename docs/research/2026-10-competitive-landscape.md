# Competitive landscape: eu-reg-mcp (October 2026)

> **Network-limited run.** Research ran on 2026-10-20 from a Claude Code cloud container with restricted egress. GitHub (clone, WebFetch of github.com pages, raw.githubusercontent.com), pypi.org, the npm registry, `registry.modelcontextprotocol.io` and web search worked. These hosts failed (DNS error `getaddrinfo ENOTFOUND`, or proxy 403) and could not be opened: eur-lex.europa.eu, www.esma.europa.eu, publications.europa.eu (CELLAR SPARQL), api.gleif.org, gateway.ansvar.eu, ansvar.eu, casptracker.eu, micarequirements.com, modelcontextprotocol.io, code.visualstudio.com, docs.cursor.com. Facts seen only in search snippets are tagged **Claimed**. Nothing was filled in from memory.

Companion documents: [feature matrix](feature-matrix.csv) · [design teardown](design-teardown.md) · [adaptation plan](adaptation-plan.md) · ADRs in [`docs/adr/`](../adr/).

## 1. Method

- **Scope.** MCP servers and tools that a crypto-asset compliance lawyer, a MiCAR white paper drafter or an AI Act assessor would put next to eu-reg-mcp, plus best-in-class MCP servers from other categories as pattern donors.
- **Evidence tags.** **Observed**: seen in source, a README, a registry record or a live response. **Claimed**: marketing, listings or search snippets only. **Inferred**: my reasoning. A row's tag is its weakest claim, in the order Observed, Claimed, Inferred (Inferred weakest). Every source was accessed on **2026-10-20** unless another date is given.
- **Reuse of sibling research.** The sibling sessions for [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter/pull/30) and [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier/pull/31) ran the same day under the same network limits. Their research on shared competitors is reused, not repeated, and cited as **[L]** (linter: `docs/research/2026-10-competitive-landscape.md` on branch `feat/competitive-adaptation-2026-10`) and **[C]** (classifier: same path and branch). Those PRs are unmerged; nothing here depends on them.
- **Clean room.** Only patterns are adapted. No code was copied (no `THIRD_PARTY_NOTICES.md` needed). Tool and parameter names are cited; no tool descriptions are reproduced. Review mining keeps complaint themes and issue numbers only.

## 2. Phase 0 baseline (2026-10-20, branch point `68303d6`)

| Measure | Value |
| --- | --- |
| Tests | 39 passed (`uv run pytest -q`); ruff, ruff format, mypy clean |
| Negotiated protocol | `2025-11-25` (mcp 1.28.1 locked; PyPI has 1.30.0 on 1.x and 2.3.0 on 2.x). Update 2026-10-30: `uv.lock` has pinned mcp 1.30.0 since 2026-10-23 (Dependabot #15); it negotiates `2025-11-25` too |
| `tools/list` | 5 tools, 3,425 bytes compact JSON (~856 tokens); no `title`; each `outputSchema` is a permissive `{"type":"object","additionalProperties":true}` |
| `resources/list`, `resources/templates/list`, `prompts/list` | all empty |
| Response bytes (MCP `CallToolResult`, fixtures) | search 1,739 · summary 1,737 · changes 2,292 · lint 19,165 · classify 41,038 · classify schema 2,694 |
| Wheel | 13,979 bytes (`eu_reg_mcp-0.1.1-py3-none-any.whl`) |
| README | 890 words; 2 clients documented (Claude Code, Claude Desktop) |
| Live register (CLI, 2026-10-20) | snapshot 2026-10-19, age 1 day, 5/5 registers fetched, 1,655 entries, 1,845 changelog records (`scripts/live_check.py`) |

Error shapes observed over MCP stdio (transcripts in git-ignored `research/_captures/baseline/`):

| Failure | Shape today |
| --- | --- |
| No network and no cache (search, changes) | `isError: true`, plain text `Error executing tool …: could not load https://…`; no code, no `notice` |
| Extra missing (lint, classify) | success result `{"available": false, "hint": …}`; no `notice` |
| Invalid JSON (lint) | success result `{"available": true, "error": …}`; no `notice` |
| Unknown `register_slug` over MCP | `isError: true`, raw Pydantic validation text (the `Literal` rejects it) |
| Unknown `--register` on the CLI | exit 0, `total_matches: 0`, no error |
| `micar-lint` timeout | `subprocess.TimeoutExpired` is not caught (code reading) |

Every gap listed in the prompt was confirmed: `micar_register_changes` lacks `snapshot_date`, `data_age_days`, `stale` and `observatory_snapshot`; the README repeats a sentence (lines 40–41); `docs/tools.md` omits `offset`; `USER_AGENT` is hardcoded to `0.1`; `__init__.py` is empty; CLI `search` has no `--offset`; `changes --limit` defaults to 20 against the tool's 50. Fixture row `a2` copies a row that is **still on the live register** (seen in the 2026-10-20 live search) while the fixture changelog marks it `removed`.

## 3. Searches (15, EN/DE/FR)

| # | Lang | Query | What it surfaced |
| --- | --- | --- | --- |
| 1 | EN | EUR-Lex MCP server | LexAPI, conformi-search-mcp, Ansvar EU Regulations |
| 2 | EN | MiCA register API ESMA crypto-asset service providers search tool | No ESMA API documented; register news |
| 3 | EN | MiCA CASP register tracker website ESMA interim register | MiCA Crypto Alliance CASP Tracker, casptracker.eu |
| 4 | DE | MCP Server EU-Recht Gesetze Claude | Ansvar German Law MCP, Lawbster, legal-text-mcp-de, rechtsinformationen-bund-de-mcp |
| 5 | FR | serveur MCP droit européen EUR-Lex | Ansvar comprehensive-eu-law-mcp, mcp-eu-sparql, mcp-eu-compliance |
| 6 | EN | Ansvar MCP gateway EU regulations | Gateway quota and OAuth (listings) |
| 7 | EN | awesome-mcp-servers legal law regulation | Legal category in awesome-mcp-servers mirrors |
| 8 | DE | MCP-Server MiCAR Krypto Register BaFin | eu-reg-mcp's own glama listing; no BaFin-register MCP |
| 9 | FR | serveur MCP Légifrance outils citation | mcp-fr-legal (`fr_validate_citation`), pylegifrance, DroitFrancaisMCP |
| 10 | EN | "32023R1114" ELI eli/reg/2023/1114/oj Markets in Crypto-Assets | CELEX/ELI for MiCAR (snippets only; EUR-Lex unreachable) |
| 11 | EN | GLEIF API lei-records licence CC0 rate limit | CC0 licence (Claimed); no rate-limit figure found |
| 12 | EN | MCP server outputSchema structuredContent isError best practices | Error results skip output validation; keep a text block (Claimed) |
| 13 | EN | conformi-search-mcp CELEX citations GitHub | `valid_at` point-in-time filter (Claimed) |
| 14 | FR | Registre MiCA ESMA prestataires PSCA outil de recherche API | No ESMA API; MiCA CASP Tracker coverage limits |
| 15 | EN | MiCA Crypto Alliance CASP tracker directory LEI filter | Tracker fields (Claimed) |

Registry searches (`registry.modelcontextprotocol.io/v0/servers?search=`, Observed): `mica` → `io.github.CSOAI-ORG/mica-crypto-mcp`, `com.micarequirements/site`; `regulation` → `eu.ansvar/eu-regulations` and Ansvar mirrors; `eur-lex` → `io.github.cyanheads/eur-lex-mcp-server` (versions 0.1.1–0.19.0); `eu-reg` → see the correction below.

> **Correction (2026-10-21 audit).** The first version of this document said the `eu-reg` search returned no entry and that eu-reg-mcp was not in the MCP Registry. That was wrong (the query result was mis-parsed). Re-run on 2026-10-21 (`/v0/servers?search=eu-reg`, HTTP 200, Observed), it returns `io.github.sebastianfoerste/eu-reg-mcp` **0.1.0** (published 2026-10-15T09:35:02Z) and **0.1.1** (published 2026-10-15T20:31:09Z, `isLatest`), plus `eu.ansvar/eu-regulations` (latest published 2026-07-13), `io.github.Ansvar-Systems/eu-regulations-mcp` 0.7.1 (2026-01-29) and `dev.cz-agents/eu-registry` (first published 2026-05-20; 0.8.0 latest, 2026-10-02). eu-reg-mcp is therefore listed; releasing 0.2.0 means publishing a new version to the existing entry.

Owner's awesome-lists: reused from [L] §A.3 (Observed there): `awesome-eu-fintech-regulation` lists only the owner's own MiCA tools; the other lists hold no third-party MiCA register or white paper tool.

## 4. Products (33 products in the matrix, one per row, plus this repo's baseline row)

### Direct competitors (MiCAR register, EU-regulation MCP, AI Act MCP)

- **Ansvar Gateway** — one hosted endpoint, OAuth signup on first request, free and paid tiers that gate fan-out and quota; verbatim source citation promised on every result. Host unreachable; facts from the archived repos' READMEs (Observed text, Claimed behaviour). [EU_compliance_MCP README](https://github.com/Ansvar-Systems/EU_compliance_MCP)
- **Ansvar archived servers** — `EU_compliance_MCP` is **archived** (retired into a private-looking fleet monorepo on 2026-07-07, per its banner); `comprehensive-eu-law-mcp` (Apache-2.0, last commit 2026-05-17) and `german-financial-regulation-mcp` still publish source. Code read (Observed): 14 tools including `about`, `check_data_freshness`, `validate_citation`; a `buildCitation` helper returning `canonical_ref`, `display_text`, `aliases`, `source_url` and a `lookup` (tool + args) for re-verification; errors are `isError: true` with a plain `Error: …` text. The pre-built database is not redistributed (TDM licensing), so self-hosting means re-ingesting.
- **ToolOracle MiCAOracle** — 20 remote-only tools around a traffic-light "MiCA readiness" score; approval of a "bridge" upgrades a token to green; Free 10 calls/day, Pro €99/month. Observed in its [README](https://github.com/ToolOracle/micaoracle) and in [L] §A.3.
- **mica-crypto-mcp** (MEOK AI Labs / CSOAI) — on PyPI and in the MCP Registry; [L] read sdist 1.0.9: the white paper tool returns a stub status. Observed via [L] and the registry record.
- **MiCA Crypto Alliance CASP Tracker** — launched 2026-08-05; directory of ESMA CASP data with LEI, home state, regulator, authorisation date, services; filters and side-by-side comparison; says ESMA stays the official source. Claimed (news snippets: [Cryptonomist](https://en.cryptonomist.ch/2026/08/05/mica-crypto-licenses-casp-tracker/)).
- **casptracker.eu** — CASP directory with weekly change pages and a glossary; describes itself as independent of ESMA; publishes an `llms.txt`. Host blocked (403); Claimed from snippets.
- **micarequirements.com MCP** (`com.micarequirements/site`) — registry record (Observed) describes a checker plus an enquiry tool handing off to a human; endpoint unreachable.
- **Lexbeam eu-ai-act-mcp** — MIT, hosted with no key and stateless; classification from structured signals the agent derives, fails closed on sparse facts, per-finding provenance, rejects unknown argument names. Observed ([README](https://github.com/lexbeam-software/eu-ai-act-mcp)); teardown in [C] §5.
- **AI Act checkers and governance suites** — FLI/artificialintelligenceact.eu checker, Holistic AI calculator, Credo AI, Saidot, trail ML (acquisition by Collibra announced 2026-10-05, `still_exists=acquired`). All hosts unreachable; rows reused from [C] (Claimed).

### Adjacent products (legal data over MCP)

- **cyanheads eur-lex-mcp-server** — Apache-2.0, npm and remote, 7 tools, 2 resource templates, 1 prompt; resolves CELEX/ELI/ECLI/OJ citations to CELLAR works; consolidated-version detection (`is_superseded`); empty results come with a `notice` on how to broaden; per-tool typed error codes such as `not_found`, `invalid_date_range`, `offset_past_window`, `sparql_timeout`. Observed ([README](https://github.com/cyanheads/eur-lex-mcp-server), registry 0.19.0).
- **mcp-eu-sparql** — MIT; CELLAR SPARQL and GDPRhub; every response carries `structuredContent.citations` (title, url, celex, ecli, date, licence flag); an offline "drift" check keeps instructions consistent with tools and error codes. Observed ([README](https://github.com/matematicsolutions/mcp-eu-sparql)).
- **conformi-search-mcp** — MIT per listings; CELEX numbers with EUR-Lex links, a `valid_at` date filter; semantic search metered behind a key. Claimed (repo raw path 404; [glama listing](https://glama.ai/mcp/servers/conformi-eu/conformi-search-mcp)).
- **LexAPI** (`@lexapi/mcp`) — ten tools incl. citation graphs; free key required. Claimed ([mcp.so](https://mcp.so/servers/lexapi-mcp?tab=tools)).
- **Lex (i.AI)** — MIT; UK legislation, amendments as a searchable dataset; MCP generated from FastAPI routes (`FastMCP.from_fastapi`); PostHog analytics client in the backend; README says experimental, not for production. Observed (code at `a31684d`).
- **mcp-server-legifrance** — MIT; three search tools over the Légifrance API (key required) and one prompt that tells the model to cite official links in the body text. Errors return as ordinary text without `isError`. Raw paths under `rdassignies/` and `pylegifrance/` serve identical content, so the repo appears transferred (Inferred). Observed (code at `3c20aa7`).
- **mcp-fr-legal** — offline French corpus with `fr_validate_citation` (exists and in force). Claimed (search #9).
- **COMPL-AI** — Apache-2.0 AI Act technical interpretation plus benchmarks. Observed README; not an MCP server.
- **OpenSanctions yente** — MIT; entity matching API returning `score`, a `match` boolean against a threshold, and per-feature subscores with explanations. Observed (code at `9a2bb5e`, `yente/scoring.py`, `yente/data/common.py`).
- **eurlex (Python)** — MIT; fetch by CELEX and parse articles into a DataFrame. Observed README.
- **CUBE**, **Regology** — seed-list names only; hosts unreachable and no snippet read, so every cell in their matrix rows is `unknown` (an earlier version filled some cells without a source; corrected 2026-10-21).
- **cz-agents eu-registry** (`dev.cz-agents/eu-registry`, MIT per npm) — added 2026-10-21 after the audit: EU/EEA company lookup across 16 countries via national registries, GLEIF/LEI and VIES; npm and a hosted endpoint; caches GLEIF responses in SQLite with a 7-day default TTL. Not a MiCAR register tool, but the closest precedent for H8 (GLEIF enrichment). Observed ([README](https://github.com/martinhavel/cz-agents-mcp/tree/main/packages/eu-registry), registry record).

### Pattern donors

- **GitHub MCP Server** — toolsets via `--toolsets`/`GITHUB_TOOLSETS`, read-only mode, toolsets include resources and prompts. Observed README.
- **Cloudflare MCP** — results capped at ~6,000 tokens by default, valid JSON kept, every cut marked; opt-out via `?truncateToolResult=false`. Observed README.
- **Context7** — resolve-then-fetch pair (`resolve-library-id`, `query-docs`); docs for 30+ clients (Claimed in README).
- **Exa MCP Server** — anonymous hosted endpoint with rate limits; `?tools=` selects tools. Observed README.
- **Sentry MCP** — unit tests, evals and manual testing as three suites; evals need a key. Observed README.
- **MCP Everything** — exercises every primitive; its README already describes the 2026-07-28 stateless revision. Observed.
- **eyecite** (BSD-2) — typed citation objects with spans and `annotate_citations`. Observed README.
- **Cobalt** (LGPL-3.0, pattern only) — FRBR URIs with expression dates for point-in-time. Observed README.

## 5. Review mining (complaint themes, first page of each tracker)

- **github-mcp-server** ([issues](https://github.com/github/github-mcp-server/issues?q=is%3Aissue+context+tokens)): excessive context from tool lists and large responses (#1286, #2383, #957); requests to paginate or filter large results (#567, #1297, #1306); remote setup and OAuth failures in Claude Desktop (#799, #1404).
- **context7** ([issues](https://github.com/upstash/context7/issues?q=is%3Aissue+outdated+OR+wrong+OR+stale)): a stream of stale-content refresh requests and stale snippets after deletions (#3309, #3447); a version-pinned lookup returning the wrong source (#3446). Theme: freshness must be visible per answer.
- **Lex** ([issues](https://github.com/i-dot-ai/lex/issues)): timeouts in Claude Code (#15), a disabled case-law endpoint (#16), unclear filter types (#17), requests for full data dumps (#9).
- **Ansvar EU_compliance_MCP** ([issues](https://github.com/Ansvar-Systems/EU_compliance_MCP/issues?q=is%3Aissue)): empty `source_url` and effective dates on returned provisions (#35, #71, #80), missing version history (#70), a connection failure (#15). Theme: provenance fields that exist in the schema but come back empty.

## 6. Context, verified where reachable

- **MCP 2026-07-28** (Observed, [changelog](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/changelog.mdx)): stateless protocol (no `initialize`; version and capabilities per request); `inputSchema`/`outputSchema` accept any JSON Schema 2020-12; Roots, Sampling and Logging deprecated; multi-round-trip requests replace server-initiated requests.
- **Python SDK** (Observed, PyPI): `mcp` 2.3.0 is current; 1.x continues (1.30.0). This repo locked 1.28.1 on 2026-10-20 and negotiates `2025-11-25`. Update 2026-10-30: `uv.lock` has pinned 1.30.0 since 2026-10-23 (Dependabot #15), which negotiates the same version.
- **Observatory** (Observed, git tree): `data/snapshots/` holds 16 dated files from 2026-07-07 to 2026-10-19, **not all on a 7-day rhythm** (2026-07-13); there is no index file, so a client cannot discover dated snapshots without listing the repo.
- **Sibling releases** (Observed, PyPI): micar-whitepaper-linter 0.2.1 and eu-ai-act-classifier 0.2.1; this repo locked 0.2.0 of both on 2026-10-20. Update 2026-10-30: `uv.lock` pins micar-whitepaper-linter 1.2.1 (since 2026-10-29, #29) and eu-ai-act-classifier 0.2.2 (since 2026-10-23, #23).
- **MiCAR identifiers** (Claimed, search #10): CELEX `32023R1114`, ELI `http://data.europa.eu/eli/reg/2023/1114/oj`. **Not verified** against EUR-Lex (unreachable), so no link ships (rule: unverifiable means no link).
- **GLEIF** (Claimed, search #11): data under CC0; throttling exists (HTTP 429) but no documented rate was found; API unreachable.

## 7. Coverage against the prompt

| Requirement | Result |
| --- | --- |
| ≥12 searches EN/DE/FR | 15: 10 EN, 2 DE (#4, #8), 3 FR (#5, #9, #14) |
| ≥15 products | 33 products, one per row (bundled rows split on 2026-10-21) |
| ≥8 teardowns incl. Ansvar, Lex, Légifrance | 8 in [design-teardown.md](design-teardown.md) |
| Code read for ≥3 OSS projects | 4: Ansvar comprehensive-eu-law-mcp, mcp-server-legifrance, yente, Lex |
| Review mining for ≥3 products | 4: github-mcp-server, context7, Lex, Ansvar |
| Ansvar Gateway live check | **Shortfall**: host unreachable; archived source and READMEs used |

## 8. Not reachable (2026-10-20)

| Host | Error | Effect |
| --- | --- | --- |
| eur-lex.europa.eu | `getaddrinfo ENOTFOUND` | No citation link or CELEX/ELI verified; D2 ships nothing |
| www.esma.europa.eu | curl status 000 (proxy refusal) | Register facts only via the observatory mirror |
| publications.europa.eu (CELLAR SPARQL) | status 000 | ELI mapping unverified |
| api.gleif.org | status 000 | H8 parked |
| gateway.ansvar.eu, ansvar.eu | `ENOTFOUND` / 000 | Gateway not inspected live |
| casptracker.eu | proxy 403 (`connect_rejected`) | Tracker rows Claimed |
| micarequirements.com | status 000 | Registry record only |
| modelcontextprotocol.io | status 000 | Spec read from GitHub instead |
| code.visualstudio.com, docs.cursor.com | `ENOTFOUND` | VS Code and Cursor configs not given. On 2026-10-21 the Zed, Gemini CLI, Continue and goose docs were read on GitHub instead, and [docs/clients.md](../clients.md) was written from them |
| holisticai.com, credo.ai, saidot.ai, trail-ml.com, artificialintelligenceact.eu, cube.global, regology.com | not retried; failed for [C] and [L] the same day | Rows Claimed or unknown |
| raw README of conformi-eu/conformi-search-mcp | HTTP 404 | Row Claimed |
