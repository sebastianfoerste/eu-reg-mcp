# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test     # core tests; classifier and linter tests skip
make install-all && make test # with the classify and lint extras
make smoke                    # install this checkout with uvx and list tools over MCP stdio
make run                      # start the server over stdio
```

Tests run offline against the fixtures in `tests/fixtures/`. `make smoke` runs `scripts/smoke_list_tools.py`; CI runs it on pushes to main, on pull requests, weekly on Mondays and on manual dispatch, and each run installs fresh with uvx and ignores uv.lock. These fixtures are small **synthetic** snapshots, not real register data. The server itself is MIT-licensed.
