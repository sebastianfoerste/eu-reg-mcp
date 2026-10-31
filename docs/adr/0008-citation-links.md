# 0008. Verified EUR-Lex citation links

- **Status:** Proposed; owner decision (the "unverifiable" blocker lifted on 2026-10-31, see the update below).
- **Date:** 2026-10-20

## Context

Sibling findings cite as plain strings (`Anhang I Teil A MiCAR`, `Annex III(4)(a) AIA`). cyanheads resolves CELEX/ELI/ECLI; mcp-eu-sparql attaches a URL per citation. eur-lex.europa.eu and publications.europa.eu were unreachable on 2026-10-20; CELEX `32023R1114` and ELI `http://data.europa.eu/eli/reg/2023/1114/oj` were seen only in search snippets.

### Update (2026-10-31)

Instrument-level identifiers can now be verified. eur-lex.europa.eu still answered this session's `curl` requests with HTTP 202 challenge pages and data.europa.eu with HTTP 500, but the Publications Office's SPARQL endpoint (`https://publications.europa.eu/webapi/rdf/sparql`, queried on `cdm:resource_legal_id_celex`, `cdm:resource_legal_eli`, `cdm:resource_legal_date_entry-into-force` and the Official Journal work) returned on 2026-10-31:

- MiCAR: CELEX `32023R1114`, ELI `http://data.europa.eu/eli/reg/2023/1114/oj`, published in OJ L 150 of 9.6.2023 (work `oj:JOL_2023_150_R`; the page range was not checked). ESMA's MiCA page links the same CELEX.
- AI Act: CELEX `32024R1689`, ELI `http://data.europa.eu/eli/reg/2024/1689/oj`; consolidated version of 27 July 2026: CELEX `02024R1689-20260727`, ELI `http://data.europa.eu/eli/reg/2024/1689/2026-07-27`. The Commission's AI Act Service Desk shows its article texts "based on the EUR-Lex consolidated version of the AI Act as at 27 July 2026".
- Digital Omnibus on AI: CELEX `32026R1744`, ELI `http://data.europa.eu/eli/reg/2026/1744/oj`, OJ L of 24.7.2026, entry into force 27.7.2026.
- Commission Implementing Regulation (EU) 2024/2984 (white paper forms, formats and templates): CELEX `32024R2984`, ELI `http://data.europa.eu/eli/reg_impl/2024/2984/oj`.

`eu-reg://about` now lists the first three under `legal_sources` (static data with a `verified_on` date; nothing is fetched at runtime). Per-finding links keyed by citation string remain this ADR's open decision, so the status stays Proposed.

## Decision (proposed)

- Add a sibling `citation_links` array next to `report` or `classification`, keyed by the exact citation string, with instrument, article, paragraph, point, CELEX, ELI, URL and `verified_on`. Leave sibling objects byte-identical; omit any citation not parsed or not verified.
- Keep a small, versioned mapping table in the repo, each row verified against EUR-Lex with its retrieval date; pin consolidated versions by their CELEX consolidation suffix.
- Ship nothing until each link is verified.

## Consequences

- Better: the linter or classifier could emit links themselves (sibling follow-up), avoiding a parser here.
