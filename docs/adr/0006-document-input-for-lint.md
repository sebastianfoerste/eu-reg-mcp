# 0006. PDF, DOCX and XHTML input for the linter

- **Status:** Proposed; owner decision.
- **Date:** 2026-10-20

## Context

`micar-lint` 0.2.0 reads PDF, DOCX, XHTML and Markdown and has `--type`, `--lang`, `--strict` and remediation, coverage and review-table outputs; the tool accepts only a JSON string. DOCX needs `python-docx`, which `eu-reg-mcp[lint]` does not install. Over HTTP, a path argument would let a remote client read server files.

## Decision (proposed)

- Accept `document_base64` plus `filename` (extension selects the reader) on all transports; write it to a temp file and delete it afterwards. Never accept a server-side path.
- Accept `whitepaper_type` and `language` mapped to `--type` and `--lang`; return remediation, coverage and review-table JSON from temp files beside the report, unchanged.
- Add `python-docx` to the `lint` extra; cap decoded size (e.g. 10 MB) with `invalid_input` beyond it.
- First bump the lock to micar-whitepaper-linter 0.2.1.

## Consequences

- Larger `tools/list` (new parameters) and larger responses; budget test must be revisited.
- Deterministic and local: `openWorldHint` stays false.
