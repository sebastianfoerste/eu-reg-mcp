# 0009. Release workflow with Trusted Publishing

- **Status:** Proposed; owner decision.
- **Date:** 2026-10-20

## Context

The CHANGELOG's unreleased items (CLI, HTTP, provenance and now this branch) are not on PyPI, so `uvx eu-reg-mcp` runs 0.1.1 and documentation describes features users do not get. eu-reg-mcp is not listed in the MCP Registry (registry search for `eu-reg` returned nothing, 2026-10-20) although `server.json` exists.

## Decision (proposed)

- `release.yml` triggered only by `release: {types: [published]}`; `permissions: contents: read` at the top; a build job; a PyPI job and an MCP Registry job, each in a GitHub `environment` with required reviewers and `id-token: write` only there; actions pinned by SHA; no `secrets.*`.
- Version bumps touch `pyproject.toml` and both `server.json` versions together (enforced by `tests/test_release_metadata.py`); the CHANGELOG heading changes from `0.2.0 (unreleased)` to `0.2.0 (<date>)`.

## Consequences

- Owner actions: PyPI Trusted Publisher, the two environments, `mcp-publisher` namespace verification. This branch adds no workflow.
