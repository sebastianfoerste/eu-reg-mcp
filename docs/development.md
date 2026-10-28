# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test   # `make run` starts the server over stdio
make smoke                  # install this checkout with uvx and list tools over MCP stdio
```

Released versions are on [PyPI](https://pypi.org/project/eu-reg-mcp/) (install: [tools.md](tools.md#install)). To try unreleased changes on `main` without cloning, run `uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp`.

Tests run offline against the fixtures in `tests/fixtures/`. These fixtures are small **synthetic** snapshots, not real register data. Fixture LEIs contain EXAMPLE and deliberately fail the ISO 17442 check digits, so they cannot belong to a real entity. `tests/test_fixtures_synthetic.py` checks this, that fixture URLs use reserved hosts (`.example`, `example.com`, `.test`), and that the change log agrees with the snapshot. `tests/evals/` holds the contract evals: each JSON file in `tests/evals/tasks/` sets up a data state, makes one MCP call through an in-memory client and states what the answer must contain (snapshot date, `notice`, error `code`, sibling output unchanged, no compliance-style keys); `test_ranking.py` scores search on 22 fictional queries. `uv run pytest -q tests/evals` runs them alone; they need no model, key or network. The server itself is MIT-licensed.

`make smoke` runs `scripts/smoke_list_tools.py`. It needs network access, because uvx installs this checkout's dependencies, including the linter and classifier, from PyPI. CI runs it with `--check-register`, which also fetches the register snapshot, on pushes to main and on pull requests; each run installs fresh with uvx and ignores uv.lock. The weekly live-data workflow (`.github/workflows/live.yml`, Tuesdays and on manual dispatch) runs the same script against the release on PyPI that [tools.md](tools.md#install) installs.

Design background: the October 2026 competitive research is in [`docs/research/`](research/) (landscape, feature matrix, design teardown, adaptation plan), and architecture decisions are in [`docs/adr/`](adr/). Live register captures made during research stay in the git-ignored `research/_captures/`.
