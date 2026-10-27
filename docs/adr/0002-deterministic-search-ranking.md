# 0002. Deterministic, explained search ranking without new dependencies

- **Status:** Accepted, built.
- **Date:** 2026-10-20

## Context

Search returned substring or exact-LEI matches in register order, so "Orbit" could list "Orbital …" first, and a misspelt or differently suffixed name ("… Ltd" for "… plc") returned nothing without explanation. OpenSanctions yente returns a score, a match flag and per-feature explanations (MIT; `yente/scoring.py`). Rule 2 forbids anything that reads as an assessment of an entity.

## Decision

- Keep the match set exactly as before (no fuzzy widening of register answers). Order it by tiers, each with a fixed `score` and a `basis`: `exact_lei`/`exact_name` 1.0, `name_without_legal_form` 0.95, `name_prefix_words` 0.9, `whole_words` 0.85, `name_prefix` 0.8, `word_start` 0.7, `substring` 0.6. Equal scores keep register order, so `offset` paging is stable.
- With zero matches and a non-LEI query, return up to five `similar_names` (`difflib.SequenceMatcher` ratio ≥ 0.8 against the whole name or the best run of as many words as the query, after dropping trailing legal-form tokens), each labelled `"not a match"`.
- Changes gain `since`, `until`, `register_slug`, `member_state`, `entity`, `entry_id` and exact `lei` filters and `offset`/`next_offset`, and the provisional `missing` change type. Only records from the 2026-10-19 snapshot on carry `lei`; older ones are found by `entry_id`. (The first version of this ADR said changelog records carry no LEI; that was wrong.)
- Standard library only; no new runtime dependency.

## Consequences

- On 22 fictional queries, real-match hit@1 rose from 0.18 to 0.36 and hit@5 stayed at 0.36 (ranking reorders, it does not widen); the 14 zero-match queries (misspellings, other legal forms) get the intended entry first in `similar_names`, which are not matches and are measured separately. An earlier version of this ADR mixed the two into "hit@1 1.00". The benchmark was written with the algorithm and overstates real-world precision.
- Scores are documented as string matching only, in the schema, the docs and the guardrails.
- Thresholds are constants in `register.py`; changing them changes answers and should go through the ranking benchmark.
