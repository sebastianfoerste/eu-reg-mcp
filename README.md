# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)

**Let your AI agent check the ESMA MiCAR register and cite EU AI Act provisions instead of guessing — with every answer framed as a fact or a candidate flag for human review.**

Scope today: the ESMA interim MiCAR register (search, summary, change tracking), MiCAR white paper linting, and EU AI Act risk-tier classification. Other EU regulation is not covered.

## Try it

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

The command needs [uv](https://docs.astral.sh/uv/), which downloads a compatible Python (3.13 or newer) if none is installed; the first start is slower while uv installs the linter and classifier.

Then ask your agent: *"Is `<entity>` on the MiCAR register, and what format is its white paper?"* The command installs the `lint` and `classify` extras, so all five tools work; no API key is needed. To run only the three register tools, drop `[lint,classify]` from the `--from` value; the lint and classify tools then return an install hint instead of failing. A PyPI package (`uvx eu-reg-mcp`) is coming; it does not exist yet, so use the git form above. Data sources, network use and the extras: [docs/tools.md](docs/tools.md#data-sources-and-network-use).

<details>
<summary>Claude Desktop (<code>claude_desktop_config.json</code>)</summary>

```json
{
  "mcpServers": {
    "eu-reg": {
      "command": "uvx",
      "args": [
        "--from",
        "eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp",
        "eu-reg-mcp"
      ]
    }
  }
}
```

If Claude Desktop cannot find `uvx`, put its absolute path (the output of `which uvx`) in `command`.
</details>

For a scripted Claude Code session on a life insurer's pricing model, with its recording protocol, see [docs/demo/claude-code-life-insurer.md](docs/demo/claude-code-life-insurer.md) (script and protocol; run not yet recorded).

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

`micar_register_changes(change_type="removed")` returns the same kind of cited record (snapshot date, register, entity) and notes that *"the register itself does not state why"* an entry was removed. The lint and classify tools return pinpoint citations (MiCAR Annex I–III; AI Act Art. 5 / Annex III / GPAI); I have not run them for this README, so no sample is shown. [UNVERIFIED: live output of those two tools]

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

- Register data: [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory) (weekly snapshots of ESMA's public interim register: white papers and authorised CASPs under Art. 109 of Regulation (EU) 2023/1114, MiCAR, and the list of non-compliant entities)
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
