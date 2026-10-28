# 0003. Register resources, an entry template and guardrail prompts

- **Status:** Accepted, built.
- **Date:** 2026-10-20

## Context

The server exposed tools only. cyanheads eur-lex-mcp-server mirrors tool data as resource templates; mcp-server-legifrance ships a prompt that demands citations; Ansvar exposes `about` and `check_data_freshness`.

## Decision

- Resources: `eu-reg://about` (version, data files, outbound hosts, staleness threshold, installed extras, error codes, notices), `micar://summary`, `micar://changes` (50 newest), and the template `micar://entry/{entry_id}`. Register resources are dated answers with `warnings` and `notice`, built by the same code as the tools.
- Resource failures are protocol errors whose message starts with the error code (`data_unavailable: …`); the MCP resource API has no `isError`.
- Prompts `check_register_status(entity)` and `review_register_changes(since)` encode the guardrails and end with the register `NOTICE` verbatim.
- `__version__` is read from package metadata and feeds `User-Agent`, `serverInfo.version` and `about`.

## Consequences

- No rule-catalogue resource: the linter exports none (sibling follow-up).
- Prompt wording is legal-effect text and needs maintainer review.
