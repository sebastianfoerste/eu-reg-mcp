"""Pure query functions over the observatory snapshot."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
from typing import Any

MAX_RESULTS = 25

# The observatory refreshes weekly; older than this means a refresh was missed.
STALE_AFTER_DAYS = 10

OBSERVATORY_DATA_URL = (
    "https://github.com/sebastianfoerste/micar-register-observatory/blob/main/data"
)

NOTICE = (
    "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as "
    "mirrored by the MiCAR Register Observatory. No legal assessment of any "
    "entity; not legal advice."
)


def _fold(text: str) -> str:
    """Case- and accent-insensitive form: 'Société' and 'societe' match."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


def data_freshness(
    snapshot_date: str | None, today: date | None = None
) -> dict[str, Any]:
    """How old the mirrored register data is, so answers can state it."""
    today = today or date.today()
    try:
        age = (today - date.fromisoformat(str(snapshot_date))).days
    except ValueError:
        return {"snapshot_date": snapshot_date, "data_age_days": None, "stale": None}
    return {
        "snapshot_date": snapshot_date,
        "data_age_days": age,
        "stale": age > STALE_AFTER_DAYS,
    }


def _provenance(snapshot: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    return {
        **data_freshness(snapshot.get("snapshot_date"), today),
        "observatory_snapshot": f"{OBSERVATORY_DATA_URL}/latest.json",
    }


def _all_entries(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        entry
        for register in snapshot.get("registers", [])
        if register.get("fetched")
        for entry in register.get("entries", [])
    ]


# Legal-form suffixes dropped before name comparison ("Foo GmbH" ~ "Foo AG").
LEGAL_FORMS = frozenset(
    "ab ag aps as asa bv co doo eu gmbh inc kft kg limited llc ltd ltda lda nv "
    "oo ou oy oyj plc sa sarl sas se sl sp spa sro srl ug uab z".split()
)
MAX_SIMILAR = 5
SIMILAR_MIN = 0.8  # SequenceMatcher ratio; below this, names are not shown

# (score, basis) per kind of match; higher ranks first. Scores describe how
# the query string matched the name or LEI, nothing about the entity.
_EXACT_LEI = (1.0, "exact_lei")
_EXACT_NAME = (1.0, "exact_name")
_NAME_WITHOUT_LEGAL_FORM = (0.95, "name_without_legal_form")
_PREFIX_WORDS = (0.9, "name_prefix_words")
_WORDS = (0.85, "whole_words")
_PREFIX = (0.8, "name_prefix")
_WORD_START = (0.7, "word_start")
_SUBSTRING = (0.6, "substring")


def _core(folded: str) -> str:
    """Folded name without punctuation and trailing legal-form tokens."""
    text = re.sub(r"[^\w\s]", " ", folded.replace(".", ""))
    tokens = text.split()
    while len(tokens) > 1 and tokens[-1] in LEGAL_FORMS:
        tokens.pop()
    return " ".join(tokens)


def _rank(needle: str, name: str, lei: str) -> tuple[float, str] | None:
    """How the query matched; None when it did not match at all."""
    if needle == lei:
        return _EXACT_LEI
    if needle not in name:
        return None
    if needle == name:
        return _EXACT_NAME
    if _core(needle) == _core(name):
        return _NAME_WITHOUT_LEGAL_FORM
    words = re.escape(needle) + r"(?!\w)"
    if name.startswith(needle):
        return _PREFIX_WORDS if re.match(words, name) else _PREFIX
    if re.search(r"(?<!\w)" + words, name):
        return _WORDS
    if re.search(r"(?<!\w)" + re.escape(needle), name):
        return _WORD_START
    return _SUBSTRING


def _similarity(needle: str, name: str) -> tuple[float, float]:
    """SequenceMatcher ratios of the query against the best run of as many
    words as the query has, and against the whole name (the tie-break)."""
    query, words = _core(needle), _core(name).split()
    width = max(1, len(query.split()))
    whole = SequenceMatcher(None, query, " ".join(words)).ratio()
    runs = (
        " ".join(words[i : i + width]) for i in range(max(1, len(words) - width + 1))
    )
    best = max([whole, *(SequenceMatcher(None, query, run).ratio() for run in runs)])
    return best, whole


def _looks_like_lei(needle: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-z]{20}", needle))


def _sources(snapshot: dict[str, Any]) -> dict[Any, Any]:
    return {
        reg.get("slug"): reg.get("source_url") for reg in snapshot.get("registers", [])
    }


def _row(entry: dict[str, Any], sources: dict[Any, Any]) -> dict[str, Any]:
    """An entry as answers show it, with the ESMA file it came from."""
    return {
        "register": entry.get("register_slug"),
        "entry_id": entry.get("entry_id"),
        "entity_name": entry.get("entity_name"),
        "lei": entry.get("lei"),
        "member_state": entry.get("member_state"),
        "authority": entry.get("authority"),
        "whitepaper_url": entry.get("wp_url"),
        "format_class": entry.get("format_class"),
        "register_last_update": entry.get("last_update"),
        "esma_source_url": sources.get(entry.get("register_slug")),
    }


def get_entry(
    snapshot: dict[str, Any], entry_id: str, today: date | None = None
) -> dict[str, Any] | None:
    """One register entry by entry_id, or None when the snapshot lacks it."""
    for entry in _all_entries(snapshot):
        if entry.get("entry_id") == entry_id:
            return {
                **_provenance(snapshot, today),
                "entry": _row(entry, _sources(snapshot)),
                "notice": NOTICE,
            }
    return None


def search_entries(
    snapshot: dict[str, Any],
    query: str,
    register: str = "all",
    member_state: str = "",
    today: date | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    needle = _fold(query)
    state = member_state.strip().upper()
    offset = max(0, offset)
    sources = _sources(snapshot)
    in_scope = [
        entry
        for entry in _all_entries(snapshot)
        if (register == "all" or entry.get("register_slug") == register)
        and (not state or entry.get("member_state", "").upper() == state)
    ]
    ranked: list[tuple[float, int, tuple[float, str] | None, dict[str, Any]]] = []
    for position, entry in enumerate(in_scope):
        name = _fold(entry.get("entity_name", ""))
        if not needle:
            ranked.append((0.0, position, None, entry))
            continue
        hit = _rank(needle, name, _fold(entry.get("lei", "")))
        if hit is not None:
            # Equal scores keep register order, so paging stays stable.
            ranked.append((-hit[0], position, hit, entry))
    ranked.sort(key=lambda item: (item[0], item[1]))
    matches = [
        {
            **_row(entry, sources),
            "match": {"score": hit[0], "basis": hit[1]} if hit else None,
        }
        for _, _, hit, entry in ranked
    ]
    similar: list[dict[str, Any]] = []
    if not matches and needle and not _looks_like_lei(needle):
        scored = [
            (*_similarity(needle, _fold(entry.get("entity_name", ""))), position)
            for position, entry in enumerate(in_scope)
        ]
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
        for ratio, _, position in scored:
            if ratio < SIMILAR_MIN or len(similar) == MAX_SIMILAR:
                break
            entry = in_scope[position]
            similar.append(
                {
                    "entry_id": entry.get("entry_id"),
                    "entity_name": entry.get("entity_name"),
                    "register": entry.get("register_slug"),
                    "member_state": entry.get("member_state"),
                    "similarity": round(ratio, 2),
                    "label": "not a match",
                }
            )
    truncated = len(matches) > offset + MAX_RESULTS
    return {
        **_provenance(snapshot, today),
        "total_matches": len(matches),
        "offset": offset,
        "results": matches[offset : offset + MAX_RESULTS],
        "truncated": truncated,
        "next_offset": offset + MAX_RESULTS if truncated else None,
        "similar_names": similar,
        "notice": NOTICE,
    }


def summarize(snapshot: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    registers = [
        {
            "register": register.get("slug"),
            "title": register.get("title"),
            "entries": len(register.get("entries", [])),
            "fetched": register.get("fetched"),
            "esma_source_url": register.get("source_url"),
        }
        for register in snapshot.get("registers", [])
    ]
    formats = Counter(
        entry.get("format_class")
        for register in snapshot.get("registers", [])
        if register.get("kind") == "whitepaper" and register.get("fetched")
        for entry in register.get("entries", [])
    )
    return {
        **_provenance(snapshot, today),
        "registers": registers,
        "whitepaper_format_coverage": dict(formats),
        "notice": NOTICE,
    }


def recent_changes(
    changelog: list[dict[str, Any]],
    limit: int = 50,
    change_type: str = "all",
    snapshot: dict[str, Any] | None = None,
    today: date | None = None,
    *,
    since: date | None = None,
    until: date | None = None,
    register: str = "all",
    member_state: str = "",
    entity: str = "",
    entry_id: str = "",
    offset: int = 0,
) -> dict[str, Any]:
    state = member_state.strip().upper()
    name = _fold(entity)
    first, last = (str(day) if day else None for day in (since, until))
    records = [
        record
        for record in changelog
        if record.get("change") != "baseline"
        and (change_type == "all" or record.get("change") == change_type)
        and (register == "all" or record.get("register_slug") == register)
        and (not state or str(record.get("member_state", "")).upper() == state)
        and (not name or name in _fold(str(record.get("entity_name", ""))))
        and (not entry_id or record.get("entry_id") == entry_id)
        and (first is None or str(record.get("snapshot_date", "")) >= first)
        and (last is None or str(record.get("snapshot_date", "")) <= last)
    ]
    records = list(reversed(records))  # newest snapshot entries last in file
    offset = max(0, offset)
    size = max(1, min(limit, 200))
    page = [dict(record) for record in records[offset : offset + size]]
    if snapshot is not None:
        listed = {entry.get("entry_id") for entry in _all_entries(snapshot)}
        for record in page:
            record["still_listed"] = record.get("entry_id") in listed
    more = len(records) > offset + size
    return {
        **_provenance(snapshot or {}, today),
        "total_changes": len(records),
        "offset": offset,
        "changes": page,
        "next_offset": offset + size if more else None,
        "changelog_source": f"{OBSERVATORY_DATA_URL}/changelog.jsonl",
        "notice": NOTICE
        + " A 'removed' record means the entry left the register export; the "
        "register itself does not state why. 'still_listed' says whether the "
        "entry is in the latest snapshot.",
    }
