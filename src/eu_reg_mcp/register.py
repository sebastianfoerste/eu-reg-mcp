"""Pure query functions over the observatory snapshot."""

from __future__ import annotations

import unicodedata
from collections import Counter
from datetime import date
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
    sources = {
        reg.get("slug"): reg.get("source_url") for reg in snapshot.get("registers", [])
    }
    matches = []
    for entry in _all_entries(snapshot):
        if register != "all" and entry.get("register_slug") != register:
            continue
        if state and entry.get("member_state", "").upper() != state:
            continue
        name = _fold(entry.get("entity_name", ""))
        lei = _fold(entry.get("lei", ""))
        if needle and needle not in name and needle != lei:
            continue
        matches.append(
            {
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
        )
    return {
        **_provenance(snapshot, today),
        "total_matches": len(matches),
        "offset": max(0, offset),
        "results": matches[max(0, offset) : max(0, offset) + MAX_RESULTS],
        "truncated": len(matches) > max(0, offset) + MAX_RESULTS,
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
) -> dict[str, Any]:
    records = [
        record
        for record in changelog
        if record.get("change") != "baseline"
        and (change_type == "all" or record.get("change") == change_type)
    ]
    records = list(reversed(records))  # newest snapshot entries last in file
    page = [dict(record) for record in records[: max(1, min(limit, 200))]]
    if snapshot is not None:
        listed = {entry.get("entry_id") for entry in _all_entries(snapshot)}
        for record in page:
            record["still_listed"] = record.get("entry_id") in listed
    return {
        **_provenance(snapshot or {}, today),
        "total_changes": len(records),
        "changes": page,
        "changelog_source": f"{OBSERVATORY_DATA_URL}/changelog.jsonl",
        "notice": NOTICE
        + " A 'removed' record means the entry left the register export; the "
        "register itself does not state why. 'still_listed' says whether the "
        "entry is in the latest snapshot.",
    }
