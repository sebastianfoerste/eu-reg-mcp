"""Pure query functions over the observatory snapshot."""

from __future__ import annotations

from collections import Counter
from typing import Any

MAX_RESULTS = 25

NOTICE = (
    "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as "
    "mirrored by the MiCAR Register Observatory. No legal assessment of any "
    "entity; not legal advice."
)


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
) -> dict[str, Any]:
    needle = query.strip().lower()
    state = member_state.strip().upper()
    matches = []
    for entry in _all_entries(snapshot):
        if register != "all" and entry.get("register_slug") != register:
            continue
        if state and entry.get("member_state", "").upper() != state:
            continue
        name = entry.get("entity_name", "").lower()
        lei = entry.get("lei", "").lower()
        if needle and needle not in name and needle != lei:
            continue
        matches.append(
            {
                "register": entry.get("register_slug"),
                "entity_name": entry.get("entity_name"),
                "lei": entry.get("lei"),
                "member_state": entry.get("member_state"),
                "authority": entry.get("authority"),
                "whitepaper_url": entry.get("wp_url"),
                "format_class": entry.get("format_class"),
                "register_last_update": entry.get("last_update"),
            }
        )
    return {
        "snapshot_date": snapshot.get("snapshot_date"),
        "total_matches": len(matches),
        "results": matches[:MAX_RESULTS],
        "truncated": len(matches) > MAX_RESULTS,
        "notice": NOTICE,
    }


def summarize(snapshot: dict[str, Any]) -> dict[str, Any]:
    registers = [
        {
            "register": register.get("slug"),
            "title": register.get("title"),
            "entries": len(register.get("entries", [])),
            "fetched": register.get("fetched"),
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
        "snapshot_date": snapshot.get("snapshot_date"),
        "registers": registers,
        "whitepaper_format_coverage": dict(formats),
        "notice": NOTICE,
    }


def recent_changes(
    changelog: list[dict[str, Any]], limit: int = 50, change_type: str = "all"
) -> dict[str, Any]:
    records = [
        record
        for record in changelog
        if record.get("change") != "baseline"
        and (change_type == "all" or record.get("change") == change_type)
    ]
    records = list(reversed(records))  # newest snapshot entries last in file
    return {
        "total_changes": len(records),
        "changes": records[: max(1, min(limit, 200))],
        "notice": NOTICE
        + " A 'removed' record means the entry left the register export; the "
        "register itself does not state why.",
    }
