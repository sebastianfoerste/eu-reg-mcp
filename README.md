<!-- mcp-name: io.github.sebastianfoerste/eu-reg-mcp -->
# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)

**Let your AI agent check the ESMA MiCAR register and cite EU AI Act provisions instead of guessing — with every answer framed as a fact or a candidate flag for human review.**

Scope today: the ESMA interim MiCAR register (search, summary, change tracking), MiCAR white paper linting, and EU AI Act risk-tier classification. Other EU regulation is not covered.

## Try it

`eu-reg-mcp` is on [PyPI](https://pypi.org/project/eu-reg-mcp/). With [uv](https://docs.astral.sh/uv/) installed, `uvx` fetches and runs it:

```bash
claude mcp add eu-reg -- uvx eu-reg-mcp
```

Then ask your agent: *"Is `<entity>` on the MiCAR register, and what format is its white paper?"* The register tools need no API key. For all five tools, add the `lint` and `classify` extras instead:

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

Without uv, run `pip install 'eu-reg-mcp[lint,classify]'` in a Python 3.13+ virtual environment and start `eu-reg-mcp` with that environment active. Install options and network use: [docs/tools.md](docs/tools.md#install).

<details>
<summary>Claude Desktop (<code>claude_desktop_config.json</code>)</summary>

```json
{
  "mcpServers": {
    "eu-reg": {
      "command": "uvx",
      "args": ["eu-reg-mcp"]
    }
  }
}
```

For the extras, use `"args": ["--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`.
</details>

## Example output

> **Synthetic data.** Produced on 2026-10-14 by running this repo's register code (`register.search_entries` / `register.recent_changes`) against the **synthetic test fixtures** in `tests/fixtures/`, not the live register. The entity and its LEI are test data. Output shape is what a live call returns; values are not.

`search_micar_register(query="skygate")`:

```json
{
  "snapshot_date": "2026-07-07",
  "total_matches": 1,
  "results": [
    {
      "register": "other-wp",
      "entity_name": "SKYGATE Network GmbH",
      "lei": "984500BBFE52FE449926",
      "member_state": "AT",
      "authority": "FMA",
      "whitepaper_url": "WWW.SKYGATETOKEN.AT",
      "format_class": "unspecified",
      "register_last_update": "30/12/2024"
    }
  ],
  "truncated": false,
  "notice": "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as mirrored by the MiCAR Register Observatory. No legal assessment of any entity; not legal advice."
}
```

`micar_register_changes(change_type="removed")` returns the same kind of cited record (snapshot date, register, entity) and notes that *"the register itself does not state why"* an entry was removed. With the extras installed, the lint and classify tools cite the provision behind each finding, for example `Anhang I Teil A MiCAR` (MiCAR Annex I, Part A), `Art. 5(1)(f) AIA`, `Annex III(4)(a) AIA`, and `Art. 51 AIA` for a general-purpose AI model with systemic risk. Sample output from synthetic inputs: [docs/tools.md](docs/tools.md#sample-lint-and-classify-output).

## Tools

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register | — |
| `micar_register_summary` | Register totals and white paper format coverage | — |
| `micar_register_changes` | New filings, changed entries, removals | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper | `lint` extra |
| `classify_eu_ai_act_system` | AI Act risk tier with pinpoint citations | `classify` extra |

Parameters, data sources, caching and network requirements: [docs/tools.md](docs/tools.md).

## Why not just ask an LLM?

An ungrounded model can invent register entries or provisions. Here, register answers come from a dated snapshot of the public register, and lint/classification output comes from deterministic rules with citations. **Review-gated** means the output is a candidate flag pending human legal review — never a legal assessment or legal advice. Details: [docs/guardrails.md](docs/guardrails.md).

## Links

- PyPI: [eu-reg-mcp](https://pypi.org/project/eu-reg-mcp/), [micar-whitepaper-linter](https://pypi.org/project/micar-whitepaper-linter/), [eu-ai-act-classifier](https://pypi.org/project/eu-ai-act-classifier/)
- Register data: [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory) (weekly snapshots of the public ESMA register, Art. 109 VO (EU) 2023/1114)
- Linter: [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annex I–III) · Classifier: [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier) — both MIT-licensed
- Development and tests: [docs/development.md](docs/development.md)

## Part of the EU regulation as code suite

By [sebastianfoerste](https://github.com/sebastianfoerste):

- [awesome-eu-fintech-regulation](https://github.com/sebastianfoerste/awesome-eu-fintech-regulation)
- [contract-review-eval-harness](https://github.com/sebastianfoerste/contract-review-eval-harness)
- [legal-function-operating-system](https://github.com/sebastianfoerste/legal-function-operating-system)
- [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier)
- [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter)
- **eu-reg-mcp** (this repo)
- [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory)

## Caveats

Register results are public-register facts with extraction artifacts possible; lint and classification outputs are candidate flags pending human legal review. Nothing here is legal advice. MIT licensed.
