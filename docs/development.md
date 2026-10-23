# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test   # `make run` starts the server over stdio
```

Released versions are on [PyPI](https://pypi.org/project/eu-reg-mcp/) (install: [tools.md](tools.md#install)). To try unreleased changes on `main` without cloning, run `uvx --from git+https://github.com/sebastianfoerste/eu-reg-mcp eu-reg-mcp`.

Tests run offline against the fixtures in `tests/fixtures/`. These fixtures are small **synthetic** snapshots, not real register data. Fixture LEIs contain EXAMPLE and deliberately fail the ISO 17442 check digits, so they cannot belong to a real entity. `tests/test_fixtures_synthetic.py` checks this, that fixture URLs use reserved hosts (`.example`, `example.com`, `.test`), and that the change log agrees with the snapshot. The server itself is MIT-licensed.
