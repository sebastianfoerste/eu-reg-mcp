<!-- mcp-name: io.github.sebastianfoerste/eu-reg-mcp -->
# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/LICENSE)
[![Python >=3.13](https://img.shields.io/badge/python-%3E%3D3.13-blue)](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/pyproject.toml)

**Let your AI assistant answer MiCAR and EU AI Act questions with citations instead of guesses — every finding flagged for human legal review.**

Scope today: the ESMA interim MiCAR register (search, summary, change tracking), MiCAR white paper linting, and EU AI Act risk-tier classification. Other EU regulation is not covered.

## Quick start

`eu-reg-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server on [PyPI](https://pypi.org/project/eu-reg-mcp/) and requires Python 3.13 or newer. With [uv](https://docs.astral.sh/uv/) installed, add it to Claude Code:

```bash
claude mcp add eu-reg -- uvx eu-reg-mcp
```

The register tools need no API key. For all five tools, add the `lint` and `classify` extras; `--python 3.13` makes uv use Python 3.13 even where an older one is the default:

```bash
claude mcp add eu-reg -- uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

Claude Desktop and other clients: [docs/clients.md](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/clients.md). pip: [docs/tools.md](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/tools.md#install).

## Tools

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register | — |
| `micar_register_summary` | Register totals and white paper format coverage | — |
| `micar_register_changes` | New filings, changed entries, removals | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper | `lint` extra |
| `classify_eu_ai_act_system` | AI Act risk tier with pinpoint citations | `classify` extra |

## Review-gated, not legal advice

Register results are public-register facts with extraction artifacts possible; lint and classification outputs are candidate flags pending human legal review. Nothing here is legal advice. MIT licensed.

## Links

- [Overview](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/overview.md): who it's for, example output, why not just ask an LLM
- [Tools reference](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/tools.md): parameters, data sources, caching, network use, errors
- [Guardrails](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/guardrails.md) · [Development and tests](https://github.com/sebastianfoerste/eu-reg-mcp/blob/main/docs/development.md)
- Register data: [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory) (weekly snapshots of the public ESMA register, Art. 109 VO (EU) 2023/1114)
- Linter: [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (rules mapped to Annex I–III) · Classifier: [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier) — both MIT-licensed
- PyPI: [eu-reg-mcp](https://pypi.org/project/eu-reg-mcp/), [micar-whitepaper-linter](https://pypi.org/project/micar-whitepaper-linter/), [eu-ai-act-classifier](https://pypi.org/project/eu-ai-act-classifier/)
