# eu-reg-mcp

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**. Agents answering crypto or AI-compliance questions can check a live official register and cite pinpoint provisions instead of guessing.

Five tools:

| Tool | What it does | Needs |
| --- | --- | --- |
| `search_micar_register` | Look up an entity by name or LEI in the ESMA interim MiCAR register: white papers (Titles II–IV), authorised CASPs, non-compliant entities | — |
| `micar_register_summary` | Current register totals and white paper format coverage | — |
| `micar_register_changes` | Register movement: new filings, changed entries, removals (withdrawal tracking) | — |
| `lint_micar_whitepaper` | Deterministic Annex I–III lint of a draft white paper: cited candidate findings | `lint` extra |
| `classify_eu_ai_act_system` | EU AI Act risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations | `classify` extra |

Register data comes from the [MiCAR Register Observatory](https://github.com/sebastianfoerste/micar-register-observatory), which snapshots the public ESMA register weekly (Art. 109 VO (EU) 2023/1114). The linter is [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter) (35 rules mapped to Annex I–III); the classifier is [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier).

## Install

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

Note: the linter and classifier packages are source-available under their own licenses (portfolio display, reference, and evaluation use), not MIT — see their repositories before production use. Without the extras, both tools return an install hint instead of failing.

## Try it

Ask an agent with this server connected:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; call with an empty string to get the schema).

## Guardrails

Every response carries its framing: register results are **facts from a public register** with the snapshot date; lint and classification outputs are **candidate flags from deterministic rules, pending human legal review**. Extraction artifacts exist. Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer.

## Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test
```

Tests run offline against fixtures. The server itself is MIT-licensed.
