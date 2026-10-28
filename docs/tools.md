# Tools reference

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
- `classify_eu_ai_act_system(profile_json="")`: a SystemProfile as JSON. An empty string returns the classifier's schema payload in `profile_schema` (the allowed roles, Annex I sections, Annex III areas, prohibited-practice codes and excluded-use flags, plus the artifact names, dossier schema and review posture), a synthetic `example_profile` (a bank deploying a credit scoring model, Annex III point 5(b)) and a `hint` naming the required fields. A profile the classifier rejects, invalid JSON and JSON that is not an object return an `invalid_input` error (see [Typed output and errors](#typed-output-and-errors)) whose `hint` points to the empty-string call; for a rejected profile, `error` names the failing fields and `validation_errors` lists each one with its `field`, `message` and `type`. Releases up to 0.1.2 return neither `example_profile` nor `validation_errors`; [CHANGELOG.md](../CHANGELOG.md) lists the changes under 0.2.0.

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

`uv pip install` works the same way inside the environment. An MCP client can start the server by full path without activating the environment: `/path/to/.venv/bin/eu-reg-mcp` (on Windows, `.venv\Scripts\eu-reg-mcp.exe`). The lint tool runs the linter's `micar-lint` command and looks for it next to the server's Python interpreter first (the environment's `bin`, or `Scripts` on Windows), then on `PATH`; failing both, it runs the installed linter package with that interpreter (`python -m micar_linter`). Before 0.1.1 it looked only on `PATH`, so the environment had to be active.

## Data sources and network use

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots ESMA's public interim register weekly: crypto-asset white papers and authorised CASPs (Art. 109 of Regulation (EU) 2023/1114, MiCAR) and the list of non-compliant entities. The server reads the observatory's `data/latest.json` and `data/changelog.jsonl` from GitHub raw (`src/eu_reg_mcp/data.py`) and caches them in memory for one hour. The three register tools therefore need network access to GitHub; they do not contact ESMA directly. A fetch that fails with a transient error (timeout, connection error, HTTP 429 or 5xx) is tried up to three times. Each fetched copy that passes validation is also saved to disk, in `$EU_REG_MCP_CACHE_DIR` if set, else `$XDG_CACHE_HOME/eu-reg-mcp` or `~/.cache/eu-reg-mcp`. If the observatory files are unreachable or invalid, the register tools fall back to the last good copy (in memory, then on disk) and raise an error only if there is none. Before 0.1.1 a failed fetch raised an error at once, with no retry or fallback.

The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (rules mapped to Annexes I to III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier). Both are separate packages from their own repositories, MIT-licensed like this server. Without the extras, both tools return an `extra_missing` error whose `hint` says how to install them. The hint gives the `uvx --python 3.13 --from` form with both extras, the `claude mcp remove` and `claude mcp add` commands that re-register the server that way in Claude Code, and the `pip install` command for a virtual environment (see [Install](#install)).

## Sample lint and classify output

> **Synthetic inputs.** Produced on 2026-10-15 by calling both tools over MCP stdio on `uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp`, which installed eu-reg-mcp 0.1.0, micar-whitepaper-linter 0.2.0 and eu-ai-act-classifier 0.2.0 from PyPI. The inputs are made up; the outputs are abridged as noted. The classify excerpts, including the obligation list and the two further profiles, are unchanged with eu-ai-act-classifier 0.2.2, the minimum version of the `classify` extra.

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

## Typed output and errors

Each tool declares a field-level `outputSchema` for its successful answers; a
successful call returns the same object as `structuredContent` and as a JSON
text block, so clients that
read only text see the same data. `notice` is always the last key. Register
answers also carry `warnings`: empty normally, one line per data file served
from the last good cached copy after a failed refresh.

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
| `invalid_input` | Arguments failed validation (e.g. an unknown `register_slug`), the JSON did not parse or is not an object, or the SystemProfile is invalid (`validation_errors` lists the failing fields) |
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
