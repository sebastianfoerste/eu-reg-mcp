# 0009. Release workflow with Trusted Publishing

- **Status:** Proposed; owner decision.
- **Date:** 2026-10-20

## Context

The CHANGELOG's unreleased items (CLI, HTTP, provenance and now this branch) are not on PyPI, so `uvx eu-reg-mcp` ran 0.1.1 and documentation described features users did not get. (Update 2026-10-27: `main` released 0.1.2 to PyPI on 2026-10-23, but the MCP Registry still lists 0.1.1 as latest, the same drift a CI publishing job would prevent.) eu-reg-mcp is listed in the MCP Registry as `io.github.sebastianfoerste/eu-reg-mcp` 0.1.0 and 0.1.1, both published 2026-10-15 (registry API, read 2026-10-21; the first version of this ADR wrongly said it was not listed).

## Decision (proposed)

- `release.yml` triggered only by `release: {types: [published]}`; `permissions: contents: read` at the top; a build job; a PyPI job and an MCP Registry job, each in a GitHub `environment` with required reviewers and `id-token: write` only there; actions pinned by SHA; no `secrets.*`.
- Version bumps touch `pyproject.toml` and both `server.json` versions together (enforced by `tests/test_release_metadata.py`); the CHANGELOG heading changes from `0.2.0 (unreleased)` to `0.2.0 (<date>)`.

## Consequences

- Owner actions: PyPI Trusted Publisher and the two environments. The `io.github.sebastianfoerste` namespace already publishes (0.1.0 and 0.1.1 went out on 2026-10-15), so the registry job only has to publish 0.2.0 to the existing entry, now from CI via GitHub OIDC rather than by hand. This branch adds no workflow.
