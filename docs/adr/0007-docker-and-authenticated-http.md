# 0007. Docker image and authenticated remote HTTP

- **Status:** Proposed; owner decision.
- **Date:** 2026-10-20

## Context

HTTP transport has no auth and is localhost-only in practice: FastMCP 1.28.1 fixes a localhost Host/Origin allow-list at construction, so `--host 0.0.0.0` binds but refuses non-local Host headers. Exa offers an anonymous rate-limited remote; GitHub and cyanheads offer OAuth or bearer auth; Ansvar is hosted-only behind OAuth.

## Decision (proposed)

- A `Dockerfile` (python:3.13-slim, non-root, `uv sync --locked`, stdio by default) published only by the release workflow.
- For remote HTTP on 1.x: an opt-in `--auth-token-file` that enables FastMCP's `token_verifier` with a constant-time bearer check, plus an explicit `--allowed-host` list passed to `TransportSecuritySettings`. Default stays `127.0.0.1` without auth.
- No hosted endpoint run by the project.

## Consequences

- New CLI flags and docs in `SECURITY.md`; no new outbound host.
