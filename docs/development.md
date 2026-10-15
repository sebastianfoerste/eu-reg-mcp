# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test     # core tests; classifier and linter tests skip
make install-all && make test # with the classify and lint extras
make smoke                    # install this checkout with uvx and list tools over MCP stdio
make run                      # start the server over stdio
```

Released versions are on [PyPI](https://pypi.org/project/eu-reg-mcp/) (install: [tools.md](tools.md#install)). To try unreleased changes on `main` without cloning, run `uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp`.

Tests run offline against the fixtures in `tests/fixtures/`. These fixtures are small **synthetic** snapshots, not real register data.

`make smoke` runs `scripts/smoke_list_tools.py`. It needs network access, because uvx installs this checkout's dependencies, including the linter and classifier, from PyPI. CI runs it with `--check-register`, which also fetches the register snapshot, on pushes to main, on pull requests, weekly on Mondays and on manual dispatch; each run installs fresh with uvx and ignores uv.lock. The weekly and manual runs also smoke-test the release on PyPI that [tools.md](tools.md#install) installs.

The extras CI job pins Python 3.13, because uv otherwise picks the newest Python, for which the locked lxml and pydantic-core may have no wheels yet. If `make install-all` fails on a missing wheel, run `UV_PYTHON=3.13 make install-all`.

The server itself is MIT-licensed.
