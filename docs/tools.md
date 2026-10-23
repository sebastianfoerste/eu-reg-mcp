# Tools reference

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

## Parameters

- `search_micar_register(query, register_slug="all", member_state="", offset=0)`: `query` is a case- and accent-insensitive entity-name substring or an exact LEI; `register_slug` is one of `all | other-wp | emt-wp | art-wp | casps | ncasp`; `member_state` is an optional two-letter code (DE, IE, MT, …); results come 25 at a time, and `offset` skips that many matches (`truncated` says whether more follow).
- `micar_register_summary()`: no parameters.
- `micar_register_changes(limit=50, change_type="all")`: `change_type` is `all | added | changed | removed`.
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

`uv pip install` works the same way inside the environment. An MCP client can start the server by full path without activating the environment: `/path/to/.venv/bin/eu-reg-mcp` (on Windows, `.venv\Scripts\eu-reg-mcp.exe`). The lint tool runs the linter's `micar-lint` command and looks for it next to the server's Python interpreter first (the environment's `bin`, or `Scripts` on Windows), then on `PATH`; failing both, it runs the installed linter package with that interpreter (`python -m micar_linter`). Before 0.1.1 it looked only on `PATH`, so the environment had to be active.

## Data sources and network use

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The server reads the observatory's `data/latest.json` and `data/changelog.jsonl` from GitHub raw (`src/eu_reg_mcp/data.py`) and caches them in memory for one hour. The three register tools therefore need network access to GitHub; they do not contact ESMA directly. A fetch that fails with a transient error (timeout, connection error, HTTP 429 or 5xx) is tried up to three times. Each fetched copy that passes validation is also saved to disk, in `$EU_REG_MCP_CACHE_DIR` if set, else `$XDG_CACHE_HOME/eu-reg-mcp` or `~/.cache/eu-reg-mcp`. If the observatory files are unreachable or invalid, the register tools fall back to the last good copy (in memory, then on disk) and raise an error only if there is none. Before 0.1.1 a failed fetch raised an error at once, with no retry or fallback.

The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annexes I to III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier). Both are separate packages from their own repositories, MIT-licensed like this server. Without the extras, both tools return an install hint instead of failing. The hint gives the `uvx --python 3.13 --from` form with both extras, the `claude mcp remove` and `claude mcp add` commands that re-register the server that way in Claude Code, and the `pip install` command for a virtual environment (see [Install](#install)).

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
uvx eu-reg-mcp search "societe generale"       # case- and accent-insensitive
uvx eu-reg-mcp search 969500FX8K40ZDW4F377      # exact LEI
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

- search and summary answers: `snapshot_date`, `data_age_days` and `stale`
  (true when the mirrored data is more than 10 days old, i.e. a weekly refresh
  was missed), and `observatory_snapshot`, the observatory file the server
  reads (on `main`; use `snapshot_date` to find the matching revision);
- per search result, the register `entry_id` and `esma_source_url`, the ESMA
  file the entry came from; per register in the summary, its `esma_source_url`;
- change answers: `changelog_source`, the observatory change log file the
  server reads (on `main`), and per change record its `snapshot_date`,
  `entry_id` and `still_listed`: whether the entry is in the latest snapshot.
