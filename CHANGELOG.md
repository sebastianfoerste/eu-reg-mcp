# Changelog

## Unreleased

- Register answers are verifiable: each result carries its `entry_id` and the ESMA source file (`esma_source_url`); responses state `snapshot_date`, `data_age_days`, `stale` and the observatory data file used.
- Change records carry `still_listed` (is the entry in the latest snapshot).
- Name search is case- and accent-insensitive ("societe" finds "Société").
- CLI subcommands `search`, `summary`, `changes` print JSON without an MCP client.
- `--transport streamable-http` (with `--host`, `--port`) serves MCP over HTTP.
- Weekly live-data check and an unlocked PyPI install smoke test in CI.
- Tools declare read-only annotations and enum parameters (`register_slug`, `change_type`); search pages with `offset`. Minimum mcp is now 1.9 (still below 2).
- Docs pin `--python 3.13` wherever the `lint`/`classify` extras are installed with uvx.
- `classify_eu_ai_act_system` with an empty profile returns the SystemProfile JSON schema, a synthetic example profile and the required fields, instead of the classifier's lists of allowed values. Invalid fields come back in the result as `validation_errors` with the schema, not as a tool error, and a JSON value that is not an object is rejected in the result.
- Every lint and classify result carries the review notice in `notice`, install hints and input errors included.
- CI installs the checkout with uvx, lists the five tools over MCP stdio and calls classify, lint and the register summary (`scripts/smoke_list_tools.py`, `make smoke`); the weekly live-data workflow runs the same check against the PyPI release.

## 0.1.1 (2026-10-15)

- Finds `micar-lint` beside the server's own Python, so an unactivated venv works.
- Install hints for uvx and Claude Code users.
- Fetch retries and an on-disk cache for the observatory data.

## 0.1.0 (2026-10-15)

- First PyPI release: MiCAR register search, summary and changes; optional white paper linting and EU AI Act classification.
