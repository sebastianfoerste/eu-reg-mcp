# Connecting MCP clients

eu-reg-mcp is a stdio MCP server. Every client below starts it with the same
command, `uvx eu-reg-mcp`, or, for all five tools, with
`uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp`.

> **Released version.** Plain `uvx eu-reg-mcp` runs the latest PyPI release
> (0.1.2 on 2026-10-27), not unreleased changes from this repository; see
> [development.md](development.md) to run `main`.

**Tested** means the exact `command` and `args` below were started by a
scratch MCP stdio client, which completed the handshake and listed all five
tools: on 2026-10-21 against PyPI 0.1.1 (mcp 1.28.1 client) and again on
2026-10-27 against PyPI 0.1.2 (mcp 1.30.0 client). It does not mean the client
application itself was run. Each format comes from the client's official
documentation at the URL given, read on 2026-10-21.

| Client | Where the config lives | Source (read 2026-10-21) |
| --- | --- | --- |
| Claude Code | `claude mcp add`, or `.mcp.json` with `--scope project` | [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) |
| Claude Desktop | `claude_desktop_config.json` | see [Claude Desktop](#claude-desktop) below |
| Zed | settings file, `context_servers` | [zed docs/src/ai/mcp.md](https://github.com/zed-industries/zed/blob/main/docs/src/ai/mcp.md) |
| Gemini CLI | `~/.gemini/settings.json` or `.gemini/settings.json`, `mcpServers`; or `gemini mcp add` | [gemini-cli docs/tools/mcp-server.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md) |
| Continue | `.continue/mcpServers/*.yaml` | [continue docs/customize/deep-dives/mcp.mdx](https://github.com/continuedev/continue/blob/main/docs/customize/deep-dives/mcp.mdx) |
| goose | `~/.config/goose/config.yaml`, `extensions` | [goose using-extensions.md](https://github.com/block/goose/blob/main/documentation/docs/getting-started/using-extensions.md) |
| VS Code (GitHub Copilot) | `.vscode/mcp.json` or the user-profile `mcp.json` (VS Code format, `servers`); or the portable `.mcp.json` / `~/.copilot/mcp-config.json` (`mcpServers`); or `code --add-mcp` | [code.visualstudio.com, MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) (read 2026-10-31) |
| Cursor | `.cursor/mcp.json` in the project or `~/.cursor/mcp.json`, `mcpServers` | [cursor.com/docs/mcp](https://cursor.com/docs/mcp) (read 2026-10-31) |

Tested command and args (both, 2026-10-21 and 2026-10-27):

- `uvx` with `["eu-reg-mcp"]`
- `uvx` with `["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`

## Claude Code

```bash
claude mcp add eu-reg -- uvx eu-reg-mcp
# shared with the team through .mcp.json:
claude mcp add --scope project eu-reg -- uvx eu-reg-mcp
```

## Claude Desktop

`claude_desktop_config.json`:

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

## VS Code (GitHub Copilot)

VS Code documents two formats (reference read 2026-10-31). The VS Code format
lives in `.vscode/mcp.json` in the workspace or in the user-profile `mcp.json`
and defines servers in a top-level `servers` object with a `type`:

```json
{
  "servers": {
    "eu-reg": {
      "type": "stdio",
      "command": "uvx",
      "args": ["eu-reg-mcp"]
    }
  }
}
```

The same entry from the command line, which adds it to the user profile:

```bash
code --add-mcp '{"name":"eu-reg","type":"stdio","command":"uvx","args":["eu-reg-mcp"]}'
```

The portable Copilot format lives in `.mcp.json` at the workspace root or in
`$COPILOT_HOME/mcp-config.json` (fallback `~/.copilot/mcp-config.json`) and
uses a top-level `mcpServers` object, like the Claude Desktop example above.
VS Code says not to copy a configuration between the two formats without
checking its capability reference.

## Cursor

`.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` for every project
(docs read 2026-10-31):

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

For the `lint` and `classify` extras, replace the args with
`["--python", "3.13", "--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]`
in any of the formats above.

## Not covered

| Client | Tried |
| --- | --- |
| Cline | `cline/cline` docs raw path returned 404 (2026-10-21) |
| OpenAI Codex | `openai/codex` `docs/config.md` only links to developers.openai.com, not read (2026-10-21) |

No config is given for these until their own documentation can be checked.
VS Code and Cursor were in this table until 2026-10-31, when their
documentation could be read (sources in the table above).
