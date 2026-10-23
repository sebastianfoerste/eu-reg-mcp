<!-- mcp-name: io.github.sebastianfoerste/eu-reg-mcp -->
# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python >=3.13](https://img.shields.io/badge/python-%3E%3D3.13-blue)](pyproject.toml)

**Let your AI assistant answer MiCAR and EU AI Act questions with citations instead of guesses — every finding flagged for human legal review.**

Scope today: the ESMA interim MiCAR register (search, summary, change tracking), MiCAR white paper linting, and EU AI Act risk-tier classification. Other EU regulation is not covered.

## Who it's for

- **Crypto-asset compliance and legal teams** looking up entities on the ESMA interim MiCAR register (white papers, authorised CASPs, non-compliant entities) and tracking what changes on it, including removals.
- **Teams preparing MiCAR white papers** who want a deterministic Annex I–III check of a draft that returns cited candidate findings.
- **Teams assessing AI systems under the EU AI Act** who want a first-pass risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations.

It does not replace legal review: its outputs are register facts or candidate flags for a human to assess (see [Guardrails](docs/guardrails.md)).

## Try it now

There is no hosted playground. eu-reg-mcp is a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, so you try it by adding it to your own MCP client — the [Quick start](#quick-start) has the configuration for Claude Code and Claude Desktop. Then ask your assistant:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; call with an empty string to get the schema).

The first two work without extras; the third needs the `classify` extra.

## Quick start

`eu-reg-mcp` is on [PyPI](https://pypi.org/project/eu-reg-mcp/) and requires Python 3.13 or newer. With [uv](https://docs.astral.sh/uv/) installed, `uvx` fetches and runs it.

**Claude Code**

```bash
claude mcp add eu-reg -- uvx eu-reg-mcp
```

The register tools need no API key. For all five tools, add the `lint` and `classify` extras instead. They need Python 3.13+, and `--python 3.13` makes uv use it even where an older Python is the default:

```bash
claude mcp add eu-reg -- uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

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

For the extras, use `"args": ["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`.

If Claude Desktop cannot find `uvx`, put its absolute path (the output of `which uvx`) in `command`.
</details>

Without uv, run `pip install 'eu-reg-mcp[lint,classify]'` in a Python 3.13+ virtual environment and register its `eu-reg-mcp` by full path, e.g. `claude mcp add eu-reg -- /path/to/.venv/bin/eu-reg-mcp`; the environment need not be active. Install options and network use: [docs/tools.md](docs/tools.md#install).

For a scripted Claude Code session on a life insurer's pricing model, with its recording protocol, see [docs/demo/claude-code-life-insurer.md](docs/demo/claude-code-life-insurer.md) (script and protocol; run not yet recorded).

## Example output

> **Synthetic data.** Produced on 2026-10-23 by running this repo's register code (`register.search_entries`) against the **synthetic test fixtures** in `tests/fixtures/`, not the live register. The entity and its LEI are invented. Fields shown are what a live call returns; values are not.

`search_micar_register(query="testnet")` (abridged: `entry_id`, `esma_source_url`, `data_age_days`, `stale`, `observatory_snapshot` and `offset` omitted):

```json
{
  "snapshot_date": "2026-07-07",
  "total_matches": 1,
  "results": [
    {
      "register": "other-wp",
      "entity_name": "Example Testnet GmbH",
      "lei": "529900EXAMPLELEI0002",
      "member_state": "LU",
      "authority": "CSSF",
      "whitepaper_url": "WWW.EXAMPLE-TESTNET.EXAMPLE",
      "format_class": "unspecified",
      "register_last_update": "01/01/2026"
    }
  ],
  "truncated": false,
  "notice": "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as mirrored by the MiCAR Register Observatory. No legal assessment of any entity; not legal advice."
}
```

`micar_register_changes(change_type="removed")` returns the same kind of cited record (snapshot date, register, entity) and notes that *"the register itself does not state why"* an entry was removed. With the extras installed, the lint and classify tools cite the provision behind each finding, for example `Anhang I Teil A MiCAR` (MiCAR Annex I, Part A), `Art. 5(1)(f) AIA`, `Annex III(4)(a) AIA`, and `Art. 51 AIA` for a general-purpose AI model with systemic risk. Sample output from synthetic inputs: [docs/tools.md](docs/tools.md#sample-lint-and-classify-output).

## Tools and data sources

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**.

Five tools:

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
- Register data: [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory) (weekly snapshots of ESMA's public interim MiCAR register under Art. 109 of Regulation (EU) 2023/1114, covering white papers and authorised CASPs, plus the list of non-compliant entities)
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
