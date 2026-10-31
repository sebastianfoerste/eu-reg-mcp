# Tools reference

Features listed under 0.2.0 in [CHANGELOG.md](../CHANGELOG.md) are on `main` and not yet on PyPI (the latest PyPI release is 0.1.2); to run `main`, use `uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp`.

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

## Parameters

- `search_micar_register(query, register_slug="all", member_state="", offset=0)`: `query` is a case- and accent-insensitive entity-name substring or an exact LEI; `register_slug` is one of `all | other-wp | emt-wp | art-wp | casps | ncasp`; `member_state` is an optional two-letter code (DE, IE, MT, …); `offset` skips that many matches (results come 25 at a time; `truncated` says whether more follow and `next_offset` gives the next page, `null` on the last). Results are ranked, and each carries `match`: a `score` and its `basis` (`exact_lei` and `exact_name` 1.0, `name_without_legal_form` 0.95, `name_prefix_words` 0.9, `whole_words` 0.85, `name_prefix` 0.8, `word_start` 0.7, `substring` 0.6; equal scores keep register order). The score describes how the query string matched the name or LEI, nothing about the entity. When nothing matches, `similar_names` lists up to five names spelt similarly to the query (`similarity` ≥ 0.8, a `difflib` ratio after dropping legal-form suffixes such as GmbH or Ltd), each labelled `"not a match"`; LEI-shaped queries get none.
- `micar_register_summary()`: no parameters.
- `micar_register_changes(limit=50, change_type="all", since=None, until=None, register_slug="all", member_state="", entity="", entry_id="", lei="", offset=0)`: newest first. `change_type` is `all | added | changed | removed | missing`. A `missing` record is provisional: the observatory saw the entry absent from one export and records it as `removed` only if the next export also lacks it, so it is not a removal. `since` and `until` are snapshot dates (`YYYY-MM-DD`, inclusive); `entity` is a case- and accent-insensitive name substring; `lei` is an exact LEI. Only change records from the 2026-10-19 snapshot on carry an `lei` field (with `record_version`, `row_key`, `changed_fields` and others, passed through as published), so an LEI filter cannot find older changes; use `entry_id` for those. `limit` is capped at 200; page with `offset` and `next_offset`. The CLI mirrors these as `changes --type --since --until --register --member-state --entity --entry-id --lei --offset` (default `--limit` is now 50, as in the tool).
- `lint_micar_whitepaper(whitepaper_json)`: a draft white paper as a JSON string.
- `classify_eu_ai_act_system(profile_json="")`: a SystemProfile as JSON; an empty string returns the schema.

## Install

`eu-reg-mcp` is published on [PyPI](https://pypi.org/project/eu-reg-mcp/) and needs Python 3.13 or newer. The `lint` and `classify` extras add [micar-whitepaper-linter](https://pypi.org/project/micar-whitepaper-linter/) and [eu-ai-act-classifier](https://pypi.org/project/eu-ai-act-classifier/), also from PyPI.

With [uv](https://docs.astral.sh/uv/), `uvx` runs the server without a separate install step and downloads a compatible Python if none is installed:

```bash
uvx eu-reg-mcp                                      # the three register tools
uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp   # all five tools; the extras need Python 3.13+
```

For one extra, name only that one: `'eu-reg-mcp[lint]'` or `'eu-reg-mcp[classify]'`. In an MCP client's JSON config, the second command is `"command": "uvx"` with `"args": ["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`.

With pip, install into a virtual environment:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install 'eu-reg-mcp[lint,classify]'   # or, without the extras: pip install eu-reg-mcp
eu-reg-mcp                                # starts the server over stdio
```

`uv pip install` works the same way inside the environment. An MCP client can start the server by full path without activating the environment: `/path/to/.venv/bin/eu-reg-mcp` (on Windows, `.venv\Scripts\eu-reg-mcp.exe`), e.g. `claude mcp add eu-reg -- /path/to/.venv/bin/eu-reg-mcp` in Claude Code. The lint tool runs the linter's `micar-lint` command and looks for it next to the server's Python interpreter first (the environment's `bin`, or `Scripts` on Windows), then on `PATH`; failing both, it runs the installed linter package with that interpreter (`python -m micar_linter`). Before 0.1.1 it looked only on `PATH`, so the environment had to be active.

## Data sources and network use

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Arts. 109 and 110 VO (EU) 2023/1114; see [Legal currency](#legal-currency)). The server reads the observatory's `data/latest.json` and `data/changelog.jsonl` from GitHub raw (`src/eu_reg_mcp/data.py`) and caches them in memory for one hour. The three register tools therefore need network access to GitHub; they do not contact ESMA directly. A fetch that fails with a transient error (timeout, connection error, HTTP 429 or 5xx) is tried up to three times. Each fetched copy that passes validation is also saved to disk, in `$EU_REG_MCP_CACHE_DIR` if set, else `$XDG_CACHE_HOME/eu-reg-mcp` or `~/.cache/eu-reg-mcp`. If the observatory files are unreachable or invalid, the register tools fall back to the last good copy (in memory, then on disk) and raise an error only if there is none. After such a fallback, the server serves that copy without contacting GitHub for five minutes from the failed refresh (`FALLBACK_RETRY_SECONDS` in `data.py`), so an outage does not repeat the retries on every call; the first call after that tries to refresh again, and a successful refresh ends the fallback. Throughout, the answer's `warnings` name each file served this way. Before 0.1.1 a failed fetch raised an error at once, with no retry or fallback.

The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (rules mapped to Annexes I to III: 38 distinct rule IDs in version 1.2.1, which `uv.lock` pins, and 36 in 0.2.1, the oldest version the `lint` extra accepts); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier). Both are separate packages from their own repositories, MIT-licensed like this server. The lint tool checks a JSON representation of a draft; it does not validate the Inline XBRL (iXBRL) format that ESMA's MiCA page describes as the white paper format requirement under the MiCA technical standards, that is Commission Implementing Regulation (EU) 2024/2984 on forms, formats and templates for crypto-asset white papers (ESMA page and the regulation's title read 2026-10-31; see [Legal currency](#legal-currency)). Document input is an open decision ([ADR 0006](adr/0006-document-input-for-lint.md)). Without the extras, both tools return an `extra_missing` error whose `hint` says how to install them. The hint gives the `uvx --python 3.13 --from` form with both extras, the `claude mcp remove` and `claude mcp add` commands that re-register the server that way in Claude Code, and the `pip install` command for a virtual environment (see [Install](#install)).

## Legal currency

Each statement below was read from the official page named on the date given; re-check before relying on a date.

- **MiCAR register status.** ESMA's MiCA page states that Articles 109 and 110 of MiCA empower ESMA to publish a central register of crypto-asset white papers, authorised crypto-asset service providers and non-compliant entities, and that the interim register is available "as a collection of csv files until mid-2026 when it will be formally integrated into ESMA's IT systems" ([esma.europa.eu, MiCA page](https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica), read 2026-10-31, when the page still said so and showed "Last update: 30 October 2026"). The CSV file URLs may therefore change, and the observatory would then need updating. The register's legal basis is Art. 109 MiCAR (white papers, issuers of asset-referenced and e-money tokens, crypto-asset service providers) and Art. 110 MiCAR (non-compliant entities providing crypto-asset services): ESMA Interactive Single Rulebook, [Article 109](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-109-register-crypto-asset-white) and [Article 110](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-110-register-non-compliant-entities), read 2026-10-31. The `ncasp` register slug is the Art. 110 list.
- **AI Act currency.** eu-ai-act-classifier 0.2.2, which the `classify` extra requires and `uv.lock` pins, applies Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744 (Digital Omnibus on AI), published in the Official Journal L series on 24 July 2026 and in force since 27 July 2026 (Publications Office metadata for CELEX 32026R1744, read 2026-10-31 through the SPARQL endpoint `https://publications.europa.eu/webapi/rdf/sparql`, because eur-lex.europa.eu answered this session's requests with challenge pages; the Commission's [AI policy page](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai), read 2026-10-31, gives the same entry-into-force date). The application dates, as the consolidated Art. 113 shows them on the Commission's AI Act Service Desk ([Article 113](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113), "based on the EUR-Lex consolidated version of the AI Act as at 27 July 2026", read 2026-10-31):
  - Annex III high-risk systems (Chapter III, Sections 1 to 3): from 2 December 2027 (Art. 113(c)(i));
  - Annex I high-risk systems: from 2 August 2028 (Art. 113(c)(ii));
  - the new prohibitions in Art. 5(1), first subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b): from 2 December 2026 (Art. 113(a));
  - Art. 50(2) marking for providers of AI systems, including general-purpose AI systems, generating synthetic content that were placed on the market before 2 August 2026: by 2 December 2026 (Art. 111(4), [Article 111](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-111), read 2026-10-31).

  Starting points: ELI `http://data.europa.eu/eli/reg/2026/1744/oj`, the consolidated AI Act `http://data.europa.eu/eli/reg/2024/1689/2026-07-27` (both resolved through the Publications Office on 2026-10-31) and the Service Desk [timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act). The `eu-reg://about` resource lists these identifiers under `legal_sources`.
- **Lint scope.** Commission Implementing Regulation (EU) 2024/2984 lays down implementing technical standards under MiCAR "with regard to forms, formats and templates for the crypto-asset white papers" (title as recorded by the Publications Office for CELEX 32024R2984, ELI `http://data.europa.eu/eli/reg_impl/2024/2984/oj`, read 2026-10-31); ESMA's MiCA page links it as the technical standard behind the iXBRL format requirement for white papers (read 2026-10-31). `lint_micar_whitepaper` reads a JSON representation of a draft and does not validate that format.

## Sample lint and classify output

> **Synthetic inputs.** Produced on 2026-10-15 by calling both tools over MCP stdio on `uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp`, which installed eu-reg-mcp 0.1.0, micar-whitepaper-linter 0.2.0 and eu-ai-act-classifier 0.2.0 from PyPI. The inputs are made up; the outputs are abridged as noted. The classify excerpts, including the obligation list and the two further profiles, are unchanged with eu-ai-act-classifier 0.2.2, the minimum version of the `classify` extra and the one `uv.lock` pins. The lint excerpt was re-checked on 2026-10-30 with a stand-in draft that reproduces it on micar-whitepaper-linter 0.2.0 and 0.2.1: version 1.2.1, which `uv.lock` pins, also applies `COMMON.LEI_CHECK_DIGITS` and `COMMON.LEI_CONSISTENCY` (both `missing`), so its summary reads `"missing": 15` and `"total": 18`, and every finding adds `citation_en` and `sources`.

`lint_micar_whitepaper` on a `"type": "other"` draft that has only a notification date, a language statement and a one-sentence offeror section. The report's summary is `{"pass": 2, "review": 1, "missing": 13, "blockers": 11, "total": 16}`; this is the finding marked `review` (its `source_anchor` omitted):

```json
{
  "rule_id": "ANNEX_I.A",
  "citation": "Anhang I Teil A MiCAR",
  "section": "offeror",
  "label": "Information about the offeror or person seeking admission to trading",
  "severity": "BLOCKER",
  "status": "review",
  "word_count": 14,
  "issues": [
    "Section is thin: 14 words, expected at least 50.",
    "Missing review terms: name, legal form, address."
  ]
}
```

`classify_eu_ai_act_system` on a CV-screening profile (`"roles": ["provider"]`, `"annex_iii_area": "III.4.a"`). Abridged to the tier and the finding; the full response also lists 14 provider obligations (Art. 9–15, 17, 43, 47–49, 72 and 73 AIA):

```json
{
  "available": true,
  "classification": {
    "system": "cv-screening-assistant",
    "risk_tier": "high_risk",
    "disposition": "determined",
    "findings": [
      {
        "rule_id": "HIGHRISK.III.4.a",
        "citation": "Annex III(4)(a) AIA",
        "citation_verified": true,
        "title": "High-risk: Employment selection and worker management",
        "detail": "Annex III high-risk area (Art. 6(2) AIA); no derogation asserted.",
        "severity": "high",
        "tier": "high_risk"
      }
    ]
  },
  "notice": "Deterministic rule output. Every finding is a candidate gap in the submitted text pending human legal review; extraction artifacts occur. Not legal advice."
}
```

Two more profiles: workplace emotion recognition (`"prohibited_practices": ["5.1.f"]`) returns `prohibited` with `Art. 5(1)(f) AIA`; a general-purpose AI model (`"is_gpai_model": true`, `"training_flops": 3e25`) returns `Art. 51 AIA` (systemic risk, above the 10^25 FLOP presumption) with obligations under Art. 53(1)(a)–(d) and Art. 55(1)(a)–(d) AIA.

## Command line and HTTP

The same register tools work without an MCP client and print JSON:

```bash
uvx eu-reg-mcp search "<entity name>"          # case- and accent-insensitive substring
uvx eu-reg-mcp search "<20-character LEI>"     # exact LEI
uvx eu-reg-mcp search "<entity name>" --offset 25   # next page of 25
uvx eu-reg-mcp summary
uvx eu-reg-mcp changes --type removed --limit 10
```

To serve MCP over HTTP instead of stdio (for clients that connect by URL), run
`uvx eu-reg-mcp --transport streamable-http --host 127.0.0.1 --port 8000`; the
endpoint is `http://127.0.0.1:8000/mcp`. It has no authentication, so keep it on
localhost or behind your own access control. With recent mcp releases, only
requests whose Host header is `localhost`, `127.0.0.1` or `[::1]` with a port
(such as `localhost:8000`) are answered, whatever address `--host` binds to: a
reverse proxy must send such a Host header, otherwise the server returns
HTTP 421.

## Verifiable answers

Every register answer carries what you need to check it:

- search, summary and change answers: `snapshot_date`, `data_age_days` and
  `stale` (true when the mirrored data is more than 10 days old, i.e. a weekly
  refresh was missed), and `observatory_snapshot`, the observatory file the
  server reads (on `main`; use `snapshot_date` to find the matching revision);
- per search result, the register `entry_id` and `esma_source_url`, the ESMA
  file the entry came from; per register in the summary, its `esma_source_url`;
- change answers also carry `changelog_source`, the observatory change log file
  the server reads (on `main`), and per change record its `snapshot_date`,
  `entry_id` and `still_listed`: whether the entry is in the latest snapshot.
- when `stale` is true, the answer's `warnings` end with a line that says so
  in words: the snapshot date, its age in days, the 10-day threshold, that a
  weekly observatory refresh was missed and the ESMA register may have changed
  since, and to check ESMA's current file before relying on the answer; when
  the snapshot date is missing or unparsable (`stale` null), a line says the
  age is unknown. A fresh snapshot adds no line, so `warnings` is empty unless
  a cached fallback is in use. The wording is `STALE_WARNING` and
  `AGE_UNKNOWN_WARNING` in `register.py`, next to `NOTICE`.

## Typed output and errors

Each tool declares a field-level `outputSchema` for its successful answers; a
successful call returns the same object as `structuredContent` and as a JSON
text block, so clients that
read only text see the same data. `notice` is always the last key. Register
answers also carry `warnings`: empty normally; one line per data file served
from the last good cached copy after a failed refresh, then, when the snapshot
is stale or undated, one line saying so (see [Verifiable answers](#verifiable-answers)).

A failed call returns `isError: true` with this object as JSON in its text
block. It carries no `structuredContent`: the MCP spec requires
`structuredContent` to match the tool's `outputSchema`, which describes
successes, and the TypeScript SDK client checks it even on errors (`Client.callTool`,
typescript-sdk 1.x, read 2026-10-21). Clients should parse the text block:

```json
{
  "code": "data_unavailable",
  "error": "could not load https://raw.githubusercontent.com/…/latest.json: …",
  "hint": "The observatory data on raw.githubusercontent.com could not be fetched …",
  "notice": "…"
}
```

| `code` | When |
| --- | --- |
| `data_unavailable` | Register data could not be fetched and no cached copy exists |
| `extra_missing` | The `lint` or `classify` extra is not installed; `hint` says how to add it, `available` is `false` |
| `invalid_input` | Arguments failed validation (e.g. an unknown `register_slug`), the JSON did not parse or is not an object, or the SystemProfile is invalid |
| `upstream_failed` | The linter failed or printed something other than JSON (`raw_output` holds the first 5,000 characters), or any other unexpected failure inside a tool (the message names the exception) |
| `timeout` | The linter did not finish within 120 seconds |

Errors from the three register tools also carry `snapshot_date`, `data_age_days` and `stale` as `null`: there was no snapshot behind the answer. `hint` is present when there is a concrete next step. The CLI prints the same
object and exits with status 1; an unknown `--register` is rejected with
status 2. Before this change, register failures were plain-text errors without
a code, and a missing extra or invalid JSON returned an ordinary result with
`available`/`hint` or `error`.

## Resources and prompts

| URI or name | Kind | What it returns |
| --- | --- | --- |
| `eu-reg://about` | resource | Server version, the observatory files read, outbound hosts, the staleness threshold, which extras are installed, the error codes and both notices |
| `micar://summary` | resource | The same answer as `micar_register_summary` |
| `micar://changes` | resource | The 50 newest changes, as `micar_register_changes` returns them |
| `micar://entry/{entry_id}` | resource template | One entry by the `entry_id` that search results carry, with `snapshot_date`, `data_age_days`, `stale`, `warnings` and `notice`; an unknown id is an error |
| `check_register_status(entity)` | prompt | Asks the model to search the register and report the facts, the snapshot date and staleness, to treat `similar_names` as non-matches and to make no assessment of the entity |
| `review_register_changes(since="")` | prompt | Asks the model to summarise changes with their dates, to say for each removal that the register itself does not state why, and not to report a provisional `missing` record as a removal |

Resources are read-only views of the same data the tools return; every
register resource carries the snapshot date and the `notice`. A resource read
has no `isError` result, so its errors are JSON-RPC errors (code 0 in mcp
1.x). The SDK prefixes the message, so the error code appears inside it rather
than at the start, and the register `notice` follows:
`Error reading resource micar://summary: data_unavailable: could not load … Notice: …`.
For the entry template the prefix is `Error creating resource from template: `,
repeated twice by the SDK; an unknown `entry_id` gives `invalid_input`. `serverInfo.version` in the MCP handshake now reports
this package's version (it reported the MCP SDK's before).
