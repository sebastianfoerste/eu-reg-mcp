# eu-reg-mcp

[![CI](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-reg-mcp/actions/workflows/ci.yml)

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**. Agents answering crypto or AI-compliance questions can check a weekly snapshot of ESMA's interim MiCAR register and cite pinpoint provisions instead of guessing.

Five tools:

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The server reads the observatory's published snapshot and changelog from GitHub (cached for an hour), not ESMA directly, and every register answer carries its snapshot date. The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (36 rules mapped to Annex I–III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier).

## Install

One command installs the server with both optional tools and starts it. It needs [uv](https://docs.astral.sh/uv/); `uvx` fetches Python 3.13 if you do not have it. The first start is slower while uv installs the linter and classifier from their repositories.

```bash
uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

**Claude Code**

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

**Claude Desktop** (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "eu-reg": {
      "command": "uvx",
      "args": [
        "--from",
        "eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp",
        "eu-reg-mcp"
      ]
    }
  }
}
```

If Claude Desktop cannot find `uvx`, put its absolute path (the output of `which uvx`) in `command`.

No configuration and no API key. The `classify` and `lint` extras install the classifier and the linter, separate MIT-licensed packages from their own repositories. If you leave an extra out, its tool returns an install hint instead of failing; the three register tools need neither.

## Try it

Ask an agent with this server connected:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; an empty call returns the profile's JSON schema and an example, and invalid fields come back as validation errors).

## Guardrails

Every response carries its framing: register results are **facts from a public register** with the snapshot date; lint and classification outputs are **candidate flags from deterministic rules, pending human legal review**. Extraction artifacts exist. Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer.

## Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test
```

Tests run offline against fixtures. The server itself is MIT-licensed.
