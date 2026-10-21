# 0008. Verified EUR-Lex citation links

- **Status:** Proposed; blocked (unverifiable this session).
- **Date:** 2026-10-20

## Context

Sibling findings cite as plain strings (`Anhang I Teil A MiCAR`, `Annex III(4)(a) AIA`). cyanheads resolves CELEX/ELI/ECLI; mcp-eu-sparql attaches a URL per citation. eur-lex.europa.eu and publications.europa.eu were unreachable on 2026-10-20; CELEX `32023R1114` and ELI `http://data.europa.eu/eli/reg/2023/1114/oj` were seen only in search snippets.

## Decision (proposed)

- Add a sibling `citation_links` array next to `report` or `classification`, keyed by the exact citation string, with instrument, article, paragraph, point, CELEX, ELI, URL and `verified_on`. Leave sibling objects byte-identical; omit any citation not parsed or not verified.
- Keep a small, versioned mapping table in the repo, each row verified against EUR-Lex with its retrieval date; pin consolidated versions by their CELEX consolidation suffix.
- Ship nothing until each link is verified.

## Consequences

- Better: the linter or classifier could emit links themselves (sibling follow-up), avoiding a parser here.
