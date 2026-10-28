# 0004. Contract evals through an in-memory MCP client, no model

- **Status:** Accepted, built.
- **Date:** 2026-10-20

## Context

Unit tests called Python functions directly, so nothing checked what a client actually receives. Sentry MCP runs evals beside unit tests (they need a model key); mcp-eu-sparql checks offline that instructions, tools and error codes agree.

## Decision

- Golden tasks are JSON files in `tests/evals/tasks/`: a setup (fixtures, fresh, offline, cached fallback, no extras, linter timeout), one call (tool, resource or prompt) and expectations. `tests/evals/test_contract_evals.py` runs them with `mcp.shared.memory.create_connected_server_and_client_session`, so the client validates `structuredContent` against `outputSchema`.
- Every answer must keep `notice` last; register answers must carry `snapshot_date`, `data_age_days`, `stale`; no key such as `compliance_status` or `risk_score` may appear in our envelope; linter and classifier output must equal a direct call byte for byte.
- Fixtures are fictional only. No model, key or network in CI.

## Consequences

- The suite found one real gap on first run (register `invalid_input` errors lacked null provenance).
- Model-driven evals ("does the answer cite the snapshot date?") stay a spec: they need a key and network.
