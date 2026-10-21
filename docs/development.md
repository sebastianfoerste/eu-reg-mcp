# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test   # `make run` starts the server over stdio
```

Released versions are on [PyPI](https://pypi.org/project/eu-reg-mcp/) (install: [tools.md](tools.md#install)). To try unreleased changes on `main` without cloning, run `uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp`.

Tests run offline against the fixtures in `tests/fixtures/`. `tests/evals/` holds the contract evals: each JSON file in `tests/evals/tasks/` sets up a data state, makes one MCP call through an in-memory client and states what the answer must contain (snapshot date, `notice`, error `code`, sibling output unchanged, no compliance-style keys); `test_ranking.py` scores search on 22 fictional queries. `uv run pytest -q tests/evals` runs them alone; they need no model, key or network. These fixtures are small **synthetic** snapshots, not real register data. The server itself is MIT-licensed.

Design background: the October 2026 competitive research is in [`docs/research/`](research/) (landscape, feature matrix, design teardown, adaptation plan), and architecture decisions are in [`docs/adr/`](adr/). Live register captures made during research stay in the git-ignored `research/_captures/`.
