# Changelog

## 0.1.2 (2026-10-23)

- Register answers are verifiable: each search result carries its `entry_id` and the ESMA source file (`esma_source_url`), and so does each register in the summary; search and summary responses state `snapshot_date`, `data_age_days`, `stale` and the observatory data file used (`observatory_snapshot`), and change responses name the change log file (`changelog_source`).
- Change records carry `still_listed` (is the entry in the latest snapshot), so `micar_register_changes` now loads the snapshot as well as the change log.
- Name search is accent-insensitive as well as case-insensitive and treats runs of whitespace as one space ("societe" finds "Société").
- CLI subcommands `search`, `summary`, `changes` print JSON without an MCP client.
- `--transport streamable-http` (with `--host`, `--port`) serves MCP over HTTP at `/mcp`, without authentication. With recent mcp releases (such as 1.28 and 1.30), only requests with a `localhost` or `127.0.0.1` Host header are answered, whatever address `--host` binds to; others get HTTP 421.
- Weekly live-data check and an unlocked PyPI install smoke test in CI.
- Tools declare read-only annotations and enum parameters (`register_slug`, `change_type`); search pages with `offset`, 25 results at a time. An unknown `register_slug` or `change_type` is now rejected as an invalid argument; 0.1.1 returned an empty result. Minimum mcp is now 1.9 (still below 2).
- Docs, and the install hint the lint and classify tools return when their extra is missing, pin `--python 3.13` wherever the `lint`/`classify` extras are installed with uvx.
- Test fixtures and the README example, which is also the PyPI project description, use invented entities only. A fixture row copied from the live register, which the 0.1.1 README showed as synthetic search output, and the removal event invented for it in the fixture change log, are gone. A new test checks that fixture LEIs fail the check digits, fixture URLs use reserved hosts and the change log agrees with the snapshot.
- The `classify` extra requires eu-ai-act-classifier 0.2.2 or newer (was 0.2.0). Its application timeline already had the 2 December 2027 and 2 August 2028 high-risk dates and now has six more entries, among them two Regulation (EU) 2026/1744 entries dated 2 December 2026: Art. 5(1)(ba) and (bb) and Art. 5(1a) and (1b), and Art. 50(2) for generative systems placed on the market before 2 August 2026 (Art. 111(4)); the other four are dated 2 August 2025, 27 July 2026, 2 August 2027 and 2 August 2030. As the classifier's 0.2.2 upgrade notes describe, `classify_eu_ai_act_system` output changes too: `placing_on_market_date` and `putting_into_service_date` must be ISO dates (YYYY-MM-DD), so a profile with "March 2026" is rejected; some high-risk, Art. 49(3) deployer and general-purpose AI model profiles return `requires_review` instead of `determined`; the `obligation_graph` items for Arts. 40 to 44, 47 and 48, Art. 49 where it applies, and Arts. 72 and 73 are dated 2 August 2026 instead of 2 December 2027 or 2 August 2028, `review_required` and flagged "Literal reading, confirm with counsel"; and Art. 49 registration is no longer listed for a system that is high-risk only as an Annex I product or for an Annex III point 2 system. Those notes compare 0.2.2 with 0.2.1; where checked, 0.2.0 behaves like 0.2.1. Profiles may use the new fields `deployer_public_authority`, `gpai_model_placing_on_market_date` and `annex_i_section` and the prohibited-practice codes `5.1.ba` and `5.1.bb`; the schema returned for an empty `profile_json` lists the codes and adds `annex_i_sections`.
- `classify_eu_ai_act_system` returns `{"available": true, "error": ...}` instead of failing the tool call when the classifier rejects the profile (such as a non-ISO date or an unknown field) or `profile_json` is not a JSON object.
- CONTRIBUTING.md, SECURITY.md and GitHub issue forms for bugs and register data; the README drops its screenshot placeholder.

## 0.1.1 (2026-10-15)

- Finds `micar-lint` beside the server's own Python, so an unactivated venv works.
- Install hints for uvx and Claude Code users.
- Fetch retries and an on-disk cache for the observatory data.

## 0.1.0 (2026-10-15)

- First PyPI release: MiCAR register search, summary and changes; optional white paper linting and EU AI Act classification.
