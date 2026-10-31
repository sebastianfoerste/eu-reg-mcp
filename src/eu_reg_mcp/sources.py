"""Verified identifiers of the EU instruments the answers rest on.

Static data, listed by the `eu-reg://about` resource. Each identifier was
checked on `verified_on` against an official source (the Publications
Office's SPARQL endpoint and the ESMA and Commission pages named in
docs/tools.md, "Legal currency"); nothing is fetched at runtime. Per-finding
citation links remain an open decision (ADR 0008).
"""

from __future__ import annotations

VERIFIED_ON = "2026-10-31"

LEGAL_SOURCES: tuple[dict[str, str], ...] = (
    {
        "instrument": "Regulation (EU) 2023/1114 (MiCAR)",
        "celex": "32023R1114",
        "eli": "http://data.europa.eu/eli/reg/2023/1114/oj",
        "provisions": (
            "Arts. 109 and 110 (ESMA registers); Annexes I-III (white papers)"
        ),
        "verified_on": VERIFIED_ON,
    },
    {
        "instrument": (
            "Regulation (EU) 2024/1689 (AI Act), as amended by "
            "Regulation (EU) 2026/1744"
        ),
        "celex": "32024R1689",
        "eli": "http://data.europa.eu/eli/reg/2024/1689/oj",
        "consolidated_eli": "http://data.europa.eu/eli/reg/2024/1689/2026-07-27",
        "provisions": (
            "Art. 5 (prohibited practices); Art. 6 and Annex III (high-risk); "
            "Art. 50 (transparency); Arts. 51-55 (general-purpose AI models); "
            "Arts. 111 and 113 (transition and application)"
        ),
        "verified_on": VERIFIED_ON,
    },
    {
        "instrument": "Regulation (EU) 2026/1744 (Digital Omnibus on AI)",
        "celex": "32026R1744",
        "eli": "http://data.europa.eu/eli/reg/2026/1744/oj",
        "provisions": (
            "Amends Regulation (EU) 2024/1689; OJ L, 24.7.2026; in force 27.7.2026"
        ),
        "verified_on": VERIFIED_ON,
    },
)
