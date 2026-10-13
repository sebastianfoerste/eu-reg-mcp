# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**. Agents answering crypto or AI-compliance questions can check a live official register and cite pinpoint provisions instead of guessing.

**What is MCP?** The [Model Context Protocol](https://modelcontextprotocol.io) is an open-source standard for connecting AI applications such as Claude to outside tools and data; its own documentation compares it to a USB-C port for AI applications. This repository is one such tool provider: once it is connected, the assistant can check the ESMA MiCAR register or run the white paper linter itself and quote the result with its source, instead of answering from memory.

Five tools:

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annex I–III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier).

## Install

Both setups below start the server with the `lint` and `classify` extras, so all five tools work. They need [uv](https://docs.astral.sh/uv/) installed; no API key and no further configuration.

**Claude Code**

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

**Claude Desktop** (`claude_desktop_config.json`)

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

The extras install the linter and classifier from their own repositories; both are MIT-licensed like this server. To run only the three register tools, drop `[lint,classify]` from the `--from` value; the lint and classify tools then return an install hint instead of failing.

## Try it

Ask an agent with this server connected:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; call with an empty string to get the schema).

### A real tool call

Captured on 2026-10-13 from a local run: the server was installed with the uvx command above (pointed at a local checkout) and driven by a minimal MCP client. The client sent this request:

```json
{"method":"tools/call","params":{"name":"micar_register_summary","arguments":{}},"jsonrpc":"2.0","id":2}
```

The server answered with this result text, unchanged. It reflects the 2026-10-12 register snapshot; the counts move every week.

```json
{
  "snapshot_date": "2026-10-12",
  "registers": [
    {
      "register": "other-wp",
      "title": "White papers — other crypto-assets (Title II)",
      "entries": 1040,
      "fetched": true
    },
    {
      "register": "emt-wp",
      "title": "White papers — e-money tokens (Title IV)",
      "entries": 50,
      "fetched": true
    },
    {
      "register": "art-wp",
      "title": "White papers — asset-referenced tokens (Title III)",
      "entries": 0,
      "fetched": true
    },
    {
      "register": "casps",
      "title": "Authorised crypto-asset service providers (CASPs)",
      "entries": 370,
      "fetched": true
    },
    {
      "register": "ncasp",
      "title": "Non-compliant entities flagged by NCAs",
      "entries": 173,
      "fetched": true
    }
  ],
  "whitepaper_format_coverage": {
    "unspecified": 653,
    "pdf": 264,
    "xhtml/html": 171,
    "none": 2
  },
  "notice": "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as mirrored by the MiCAR Register Observatory. No legal assessment of any entity; not legal advice."
}
```

## Guardrails

Every response carries its framing: register results are **facts from a public register** with the snapshot date; lint and classification outputs are **candidate flags from deterministic rules, pending human legal review**. Extraction artifacts exist. Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer.

## Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test
```

Tests run offline against fixtures. The server itself is MIT-licensed.
