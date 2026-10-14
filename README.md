# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python >=3.13](https://img.shields.io/badge/python-%3E%3D3.13-blue)](pyproject.toml)

**Let your AI assistant answer MiCAR and EU AI Act questions with citations instead of guesses — every finding flagged for human legal review.**

<!--
  Screenshot/GIF placeholder — to be added.
  Capture a real session: Claude Code or Claude Desktop with eu-reg-mcp connected, answering
  one of the register questions under "Try it now", with the snapshot date visible in the answer.
  Then replace this comment and the note below with the image.
-->

> *Screenshot/GIF placeholder — to be added*

## Who it's for

- **Crypto-asset compliance and legal teams** looking up entities on the ESMA interim MiCAR register (white papers, authorised CASPs, non-compliant entities) and tracking what changes on it, including removals.
- **Teams preparing MiCAR white papers** who want a deterministic Annex I–III check of a draft that returns cited candidate findings.
- **Teams assessing AI systems under the EU AI Act** who want a first-pass risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations.

It does not replace legal review: its outputs are register facts or candidate flags for a human to assess (see [Guardrails](#guardrails)).

## Try it now

There is no hosted playground. eu-reg-mcp is a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, so you try it by adding it to your own MCP client — the [Quick start](#quick-start) has the configuration for Claude Code and Claude Desktop. Then ask your assistant:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; call with an empty string to get the schema).

The first two work without extras; the third needs the `classify` extra.

## Quick start

The commands below use [uv](https://docs.astral.sh/uv/); the server requires Python 3.13 or newer.

**Claude Code**

```bash
claude mcp add eu-reg -- uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp
```

**Claude Desktop** (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "eu-reg": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sebastianfoerste/eu-reg-mcp", "eu-reg-mcp"]
    }
  }
}
```

The three register tools work with no configuration and no API key. The lint and classify tools need their optional extras:

```bash
uv pip install 'eu-reg-mcp[lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'
uv pip install 'eu-reg-mcp[classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'
```

The linter and classifier are separate packages from their own repositories, MIT-licensed like this server. Without the extras, both tools return an install hint instead of failing.

## Tools and data sources

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**.

Five tools:

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annex I–III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier).

## Guardrails

Every response carries its framing: register results are **facts from a public register** with the snapshot date; lint and classification outputs are **candidate flags from deterministic rules, pending human legal review**. Extraction artifacts exist. Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer.

## Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test
```

Tests run offline against fixtures. The server itself is MIT-licensed.
