# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test     # core tests; classifier and linter tests skip
make install-all && make test # with the classify and lint extras
make smoke                    # install this checkout with uvx and list tools over MCP stdio
make run                      # start the server over stdio
```

Tests run offline against the fixtures in `tests/fixtures/`. These fixtures are small **synthetic** snapshots, not real register data.

`make smoke` runs `scripts/smoke_list_tools.py`. It needs network access, because uvx installs the linter and classifier from their repositories. CI runs it with `--check-register`, which also fetches the register snapshot, on pushes to main, on pull requests, weekly on Mondays and on manual dispatch; each run installs fresh with uvx and ignores uv.lock.

The extras CI job pins Python 3.13, because uv otherwise picks the newest Python, for which the locked lxml and pydantic-core may have no wheels yet. If `make install-all` fails on a missing wheel, run `UV_PYTHON=3.13 make install-all`.

The server itself is MIT-licensed.
