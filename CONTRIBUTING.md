# Contributing

Issues and pull requests are welcome.

## Development

```bash
uv sync --extra dev --extra lint --extra classify
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q
```

Python 3.13+. Tests run offline against `tests/fixtures/`; `scripts/live_check.py` checks the live observatory data.

## Ground rules

- Register answers must stay factual and traceable to the ESMA data (entry id, source file, snapshot date). No legal assessment of any entity.
- Changes to wording that describes legal effect (notices, hints, docs) are reviewed by the maintainer, a lawyer, before merging.
- Keep `mcp` below 2 until the server is ported.
