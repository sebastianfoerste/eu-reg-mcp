# Changelog

## Unreleased

- `micar_register_changes` now states `snapshot_date`, `data_age_days`, `stale` and `observatory_snapshot`, like search and summary.
- CLI `search --offset` pages through matches.
- Typed output: every tool declares a field-level `outputSchema` and a `title`; register answers add `warnings` (cached-fallback notes).
- One error model: failures return `isError: true` with `code` (`data_unavailable`, `extra_missing`, `invalid_input`, `upstream_failed`, `timeout`), `error`, `hint` and `notice`. A missing extra or invalid JSON is now an error result, not an ordinary one; linter timeouts are caught. The CLI prints the error and exits 1, and rejects an unknown `--register`.
- Resources `eu-reg://about`, `micar://summary`, `micar://changes` and the template `micar://entry/{entry_id}`; prompts `check_register_status` and `review_register_changes` that ask for the snapshot date and keep the review framing.
- Single-source `__version__`: the HTTP `User-Agent` and the MCP `serverInfo.version` (which reported the SDK's version) now state this package's version.
- Ranked search: each result carries `match` (`score` and `basis`, string matching only); `next_offset` pages; with no match, `similar_names` lists up to five similarly spelt names, each labelled "not a match". On a 22-query synthetic benchmark, hit@1 rose from 0.18 to 1.00.
- `micar_register_changes` filters by `since`, `until`, `register_slug`, `member_state`, `entity` and `entry_id`, and pages with `offset`/`next_offset`; the CLI mirrors them, and `changes --limit` now defaults to 50 like the tool.
- Test fixtures and the README example use only fictional entities and example LEIs; a fixture row that copied a live register entry is gone.
- Register answers are verifiable: each result carries its `entry_id` and the ESMA source file (`esma_source_url`); responses state `snapshot_date`, `data_age_days`, `stale` and the observatory data file used.
- Change records carry `still_listed` (is the entry in the latest snapshot).
- Name search is case- and accent-insensitive ("societe" finds "Société").
- CLI subcommands `search`, `summary`, `changes` print JSON without an MCP client.
- `--transport streamable-http` (with `--host`, `--port`) serves MCP over HTTP.
- Weekly live-data check and an unlocked PyPI install smoke test in CI.
- Tools declare read-only annotations and enum parameters (`register_slug`, `change_type`); search pages with `offset`. Minimum mcp is now 1.22 (still below 2): typed output and titles need it, and it is the oldest release this suite passes on.
- Docs pin `--python 3.13` wherever the `lint`/`classify` extras are installed with uvx.

## 0.1.1 (2026-10-15)

- Finds `micar-lint` beside the server's own Python, so an unactivated venv works.
- Install hints for uvx and Claude Code users.
- Fetch retries and an on-disk cache for the observatory data.

## 0.1.0 (2026-10-15)

- First PyPI release: MiCAR register search, summary and changes; optional white paper linting and EU AI Act classification.
