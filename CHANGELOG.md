# Changelog

## 0.2.0 (unreleased)

- `micar_register_changes` now states `snapshot_date`, `data_age_days`, `stale` and `observatory_snapshot`, like search and summary.
- CLI `search --offset` pages through matches.
- Typed output: every tool declares a field-level `outputSchema` and a `title`; register answers add `warnings` (cached-fallback notes).
- One error model: failures return `isError: true` with a JSON text block holding `code` (`data_unavailable`, `extra_missing`, `invalid_input`, `upstream_failed`, `timeout`), `error`, `hint` and `notice`, and no `structuredContent` (which must match the success `outputSchema`; TypeScript clients check it even on errors). Any unexpected exception inside a tool becomes `upstream_failed`. Cached-fallback `warnings` name only the data files an answer read. Resource read errors carry the code and the register `notice` in their message. A missing extra or invalid JSON is now an error result, not an ordinary one; linter timeouts are caught. The CLI prints the error and exits 1, and rejects an unknown `--register`.
- Contract evals: 25 golden tasks in `tests/evals/tasks/` run through an MCP client on fictional fixtures (dates, notice, error codes, unchanged sibling output, no compliance-style keys), plus a test that versions and the registry name agree. The heading above proposes 0.2.0; publishing stays a maintainer step.
- Errors from register tools always carry `snapshot_date`, `data_age_days` and `stale` (as `null`).
- Resources `eu-reg://about`, `micar://summary`, `micar://changes` and the template `micar://entry/{entry_id}`; prompts `check_register_status` and `review_register_changes` that ask for the snapshot date and keep the review framing.
- Single-source `__version__`: the HTTP `User-Agent` and the MCP `serverInfo.version` (which reported the SDK's version) now state this package's version.
- The `lint` and `classify` extras now require micar-whitepaper-linter 0.2.1 and eu-ai-act-classifier 0.2.1 or newer (was 0.2.0), and the lockfile uses 0.2.1.
- Ranked search: each result carries `match` (`score` and `basis`, string matching only); `next_offset` pages; with no match, `similar_names` lists up to five similarly spelt names, each labelled "not a match". On a 22-query synthetic benchmark, real-match hit@1 rose from 0.18 to 0.36 (hit@5 unchanged at 0.36, since ranking only reorders literal matches); on the 14 queries with no match, `similar_names` put the intended entry first every time, as a suggestion, not a match.
- `micar_register_changes` filters by `since`, `until`, `register_slug`, `member_state`, `entity`, `entry_id` and exact `lei` (change records carry an LEI from the 2026-10-19 snapshot on), accepts the provisional change type `missing` (explained in the answer's `notice`: not a removal), and pages with `offset`/`next_offset`; the CLI mirrors them, and `changes --limit` now defaults to 50 like the tool.
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
