# Changelog

## Unreleased

- Register answers are verifiable: each result carries its `entry_id` and the ESMA source file (`esma_source_url`); responses state `snapshot_date`, `data_age_days`, `stale` and the observatory data file used.
- Change records carry `still_listed` (is the entry in the latest snapshot).
- Name search is case- and accent-insensitive ("societe" finds "Société").
- CLI subcommands `search`, `summary`, `changes` print JSON without an MCP client.
- `--transport streamable-http` (with `--host`, `--port`) serves MCP over HTTP.
- Weekly live-data check and an unlocked PyPI install smoke test in CI.
- Docs pin `--python 3.13` wherever the `lint`/`classify` extras are installed with uvx.

## 0.1.1 (2026-10-15)

- Finds `micar-lint` beside the server's own Python, so an unactivated venv works.
- Install hints for uvx and Claude Code users.
- Fetch retries and an on-disk cache for the observatory data.

## 0.1.0 (2026-10-15)

- First PyPI release: MiCAR register search, summary and changes; optional white paper linting and EU AI Act classification.
