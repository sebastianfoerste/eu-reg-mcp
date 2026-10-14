# Tools reference

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

## Parameters

- `search_micar_register(query, register_slug="all", member_state="")` — `query` is a case-insensitive entity-name substring or an exact LEI; `register_slug` is one of `all | other-wp | emt-wp | art-wp | casps | ncasp`; `member_state` is an optional two-letter code (DE, IE, MT, …).
- `micar_register_summary()` — no parameters.
- `micar_register_changes(limit=50, change_type="all")` — `change_type` is `all | added | changed | removed`.
- `lint_micar_whitepaper(whitepaper_json)` — a draft white paper as a JSON string.
- `classify_eu_ai_act_system(profile_json="")` — a SystemProfile as JSON; an empty string returns the profile's JSON schema and an example, and invalid fields come back as validation errors.

## Data sources and network use

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The server reads the observatory's `data/latest.json` and `data/changelog.jsonl` from GitHub raw (`src/eu_reg_mcp/data.py`) and caches them in memory for one hour. The three register tools therefore need network access to GitHub; they do not contact ESMA directly. If the observatory files are unreachable, the register tools raise an error (no fallback is implemented).

The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annex I–III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier). Both are separate packages from their own repositories, MIT-licensed like this server. Without the extras, both tools return an install hint instead of failing.

```bash
uv pip install 'eu-reg-mcp[lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'
uv pip install 'eu-reg-mcp[classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'
```
