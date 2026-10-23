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
- Test fixtures and the README example use invented entities only; a fixture row copied from the live register, and the removal event invented for it, are gone. A new test checks that fixture LEIs fail the check digits, fixture URLs use reserved hosts and the change log agrees with the snapshot.
- The `classify` extra requires eu-ai-act-classifier 0.2.2 or newer (was 0.2.0). Its application timeline already had the 2 December 2027 and 2 August 2028 high-risk dates and now adds two Regulation (EU) 2026/1744 entries dated 2 December 2026: Art. 5(1)(ba) and (bb) and Art. 5(1a) and (1b), and Art. 50(2) for generative systems placed on the market before 2 August 2026 (Art. 111(4)). As the classifier's 0.2.2 upgrade notes describe, `classify_eu_ai_act_system` output changes too: `placing_on_market_date` and `putting_into_service_date` must be ISO dates (YYYY-MM-DD), so a profile with "March 2026" is rejected; some high-risk, Art. 49(3) deployer and general-purpose AI model profiles return `requires_review` instead of `determined`; the `obligation_graph` items for Arts. 40 to 44, 47 and 48, Art. 49 where it applies, and Arts. 72 and 73 are dated 2 August 2026 instead of 2 December 2027 or 2 August 2028, `review_required` and flagged "Literal reading, confirm with counsel"; and Art. 49 registration is no longer listed for a system that is high-risk only as an Annex I product or for an Annex III point 2 system.
- `classify_eu_ai_act_system` returns `{"available": true, "error": ...}` instead of failing the tool call when the classifier rejects the profile (such as a non-ISO date) or `profile_json` is not a JSON object.
- `classify_eu_ai_act_system` also returns `validation_errors` (field, message, type), the SystemProfile JSON schema and a hint when the classifier rejects the profile. An empty `profile_json` returns that schema, a synthetic example profile and the required fields, instead of the classifier's lists of allowed values.
- Every lint and classify result carries the review notice in `notice`, install hints and input errors included.
- CI installs the checkout with uvx, lists the five tools over MCP stdio and calls classify, lint and the register summary (`scripts/smoke_list_tools.py --check-register`); `make smoke` runs the same check without the register call. The weekly live-data workflow runs the check, register call included, against the PyPI release.

## 0.1.1 (2026-10-15)

- Finds `micar-lint` beside the server's own Python, so an unactivated venv works.
- Install hints for uvx and Claude Code users.
- Fetch retries and an on-disk cache for the observatory data.

## 0.1.0 (2026-10-15)

- First PyPI release: MiCAR register search, summary and changes; optional white paper linting and EU AI Act classification.
