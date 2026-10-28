# 0005. Point-in-time `as_of` queries

- **Status:** Proposed; blocked on the observatory.
- **Date:** 2026-10-20

## Context

The observatory publishes dated snapshots at `data/snapshots/<YYYY-MM-DD>.json` (16 files from 2026-07-07 to 2026-10-19, Observed in its git tree) but no index, and the dates are not strictly weekly (2026-07-13). The changelog skips quiet weeks. Rebuilding past states from the changelog is ruled out.

## Decision (proposed)

- Add `as_of: date` to search and summary once the observatory publishes `data/snapshots/index.json`. The server reads the index (cached), picks the latest snapshot on or before `as_of`, fetches and caches it on disk like `latest.json`, and answers with that snapshot's date plus `as_of` echoed.
- Without an index, do nothing: probing dates blind costs up to seven 0.6–2.8 MB fetches per query.

## Consequences

- Sibling follow-up recorded in the adaptation plan. Outbound host stays raw.githubusercontent.com.
