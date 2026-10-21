# Connecting MCP clients

eu-reg-mcp is a stdio MCP server. Every client below starts it with the same
command, `uvx eu-reg-mcp`, or, for all five tools, with
`uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp`.

> **Released version.** Plain `uvx eu-reg-mcp` runs the latest PyPI release
> (0.1.1 on 2026-10-21), not unreleased changes from this repository; see
> [development.md](development.md) to run `main`.

**Tested** means the exact `command` and `args` below were started on
2026-10-21 by a scratch MCP stdio client (mcp 1.28.1), which completed the
handshake and listed all five tools from PyPI 0.1.1. It does not mean the
client application itself was run. Each format comes from the client's
official documentation at the URL given, read on 2026-10-21.

| Client | Where the config lives | Source (read 2026-10-21) |
| --- | --- | --- |
| Claude Code | `claude mcp add`, or `.mcp.json` with `--scope project` | [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) |
| Claude Desktop | `claude_desktop_config.json` | see the [README](../README.md#quick-start) |
| Zed | settings file, `context_servers` | [zed docs/src/ai/mcp.md](https://github.com/zed-industries/zed/blob/main/docs/src/ai/mcp.md) |
| Gemini CLI | `~/.gemini/settings.json` or `.gemini/settings.json`, `mcpServers`; or `gemini mcp add` | [gemini-cli docs/tools/mcp-server.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md) |
| Continue | `.continue/mcpServers/*.yaml` | [continue docs/customize/deep-dives/mcp.mdx](https://github.com/continuedev/continue/blob/main/docs/customize/deep-dives/mcp.mdx) |
| goose | `~/.config/goose/config.yaml`, `extensions` | [goose using-extensions.md](https://github.com/block/goose/blob/main/documentation/docs/getting-started/using-extensions.md) |

Tested command and args (both, 2026-10-21):

- `uvx` with `["eu-reg-mcp"]`
- `uvx` with `["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`

## Claude Code

```bash
claude mcp add eu-reg -- uvx eu-reg-mcp
# shared with the team through .mcp.json:
claude mcp add --scope project eu-reg -- uvx eu-reg-mcp
```

## Zed

```json
{
  "context_servers": {
    "eu-reg": {
      "command": "uvx",
      "args": ["eu-reg-mcp"],
      "env": {}
    }
  }
}
```

## Gemini CLI

```bash
gemini mcp add eu-reg uvx eu-reg-mcp
```

or in `settings.json`:

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

## Continue

`.continue/mcpServers/eu-reg.yaml` (MCP works in agent mode only, per Continue's docs):

```yaml
name: eu-reg
version: 0.0.1
schema: v1
mcpServers:
  - name: eu-reg
    command: uvx
    args:
      - eu-reg-mcp
```

## goose

`~/.config/goose/config.yaml`:

```yaml
extensions:
  eu-reg:
    name: eu-reg
    cmd: uvx
    args: [eu-reg-mcp]
    enabled: true
    type: stdio
    timeout: 300
```

For the `lint` and `classify` extras, replace the args with
`["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`
in any of the formats above.

## Not covered (docs not readable on 2026-10-21)

| Client | Tried |
| --- | --- |
| VS Code (GitHub Copilot) | code.visualstudio.com (DNS failure); `microsoft/vscode-docs` raw paths returned 404 |
| Cursor | docs.cursor.com (DNS failure) |
| Cline | `cline/cline` docs raw path returned 404 |
| OpenAI Codex | `openai/codex` `docs/config.md` only links to developers.openai.com, not read |

No config is given for these until their own documentation can be checked.
