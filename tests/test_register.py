import json
from pathlib import Path

from eu_reg_mcp.register import recent_changes, search_entries, summarize

FIXTURES = Path(__file__).parent / "fixtures"

SNAPSHOT = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
CHANGELOG = [
    json.loads(line)
    for line in (FIXTURES / "changelog.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]


def test_search_by_name_substring():
    result = search_entries(SNAPSHOT, "testnet")
    assert result["total_matches"] == 1
    assert result["results"][0]["entity_name"] == "Example Testnet GmbH"
    assert "notice" in result


def test_search_by_exact_lei():
    result = search_entries(SNAPSHOT, "529900EXAMPLELEI0001")
    assert result["total_matches"] == 1
    assert result["results"][0]["member_state"] == "DE"


def test_search_filters_by_register_and_member_state():
    assert search_entries(SNAPSHOT, "casp", register="casps")["total_matches"] == 1
    assert search_entries(SNAPSHOT, "casp", member_state="DE")["total_matches"] == 0


def test_empty_query_lists_register_with_filters():
    result = search_entries(SNAPSHOT, "", register="other-wp")
    assert result["total_matches"] == 2


def test_summary_counts_and_coverage():
    summary = summarize(SNAPSHOT)
    assert summary["snapshot_date"] == "2026-07-07"
    totals = {r["register"]: r["entries"] for r in summary["registers"]}
    assert totals == {"other-wp": 2, "casps": 1}
    assert summary["whitepaper_format_coverage"] == {
        "xhtml/html": 1,
        "unspecified": 1,
    }


def test_changes_exclude_baseline_and_filter_by_type():
    result = recent_changes(CHANGELOG, limit=10)
    assert result["total_changes"] == 4
    assert result["changes"][0]["change"] in {"changed", "missing"}
    removed = recent_changes(CHANGELOG, change_type="removed")
    assert removed["total_changes"] == 1
    assert removed["changes"][0]["entity_name"] == "Example Withdrawn AG"


def test_search_is_accent_and_case_insensitive():
    accented = {
        "snapshot_date": "2026-07-07",
        "registers": [
            {
                "slug": "casps",
                "source_url": "https://esma.example/CASPS.csv",
                "fetched": True,
                "entries": [
                    {
                        "entry_id": "x1",
                        "register_slug": "casps",
                        "entity_name": "Société Exemple-Forge",
                    }
                ],
            }
        ],
    }
    assert search_entries(accented, "SOCIETE exemple")["total_matches"] == 1
    assert search_entries(accented, "société")["total_matches"] == 1


def test_search_results_are_verifiable():
    from datetime import date

    result = search_entries(SNAPSHOT, "testnet", today=date(2026, 7, 10))
    hit = result["results"][0]
    assert hit["entry_id"]
    assert hit["esma_source_url"].startswith("https://")
    assert result["snapshot_date"] == "2026-07-07"
    assert result["data_age_days"] == 3
    assert result["stale"] is False
    assert result["observatory_snapshot"].endswith("/data/latest.json")


def test_stale_flag_after_missed_refresh():
    from datetime import date

    assert search_entries(SNAPSHOT, "", today=date(2026, 8, 1))["stale"] is True
    assert summarize(SNAPSHOT, today=date(2026, 8, 1))["data_age_days"] == 25


def test_changes_flag_whether_entry_is_still_listed():
    result = recent_changes(CHANGELOG, change_type="all", snapshot=SNAPSHOT)
    listed = {
        entry["entry_id"]
        for reg in SNAPSHOT["registers"]
        for entry in reg.get("entries", [])
    }
    for record in result["changes"]:
        assert record["still_listed"] == (record["entry_id"] in listed)
    by_change = {r["change"]: r["still_listed"] for r in result["changes"]}
    assert by_change == {
        "added": True,
        "removed": False,
        "changed": True,
        "missing": False,  # absent from this export, so not listed
    }
    assert "still_listed" not in recent_changes(CHANGELOG)["changes"][0]


def test_change_filters():
    from datetime import date

    def ids(**filters):
        return [c["entry_id"] for c in recent_changes(CHANGELOG, **filters)["changes"]]

    newest_first = ["a4", "a1", "a3", "a2"]
    assert ids(since=date(2026, 7, 7), until=date(2026, 7, 7)) == newest_first
    assert ids(until=date(2026, 7, 6)) == []
    assert ids(since=date(2026, 7, 8)) == []
    # Every fixture change shares one snapshot date, so move two of them a week
    # earlier to check that since/until split the log rather than all-or-nothing.
    spread = [
        {**record, "snapshot_date": "2026-06-30"}
        if record["entry_id"] in {"a2", "a3"}
        else record
        for record in CHANGELOG
    ]

    def spread_ids(**filters):
        return [c["entry_id"] for c in recent_changes(spread, **filters)["changes"]]

    assert spread_ids(until=date(2026, 6, 30)) == ["a3", "a2"]
    assert spread_ids(since=date(2026, 7, 1)) == ["a4", "a1"]
    assert spread_ids(since=date(2026, 6, 30), until=date(2026, 6, 30)) == ["a3", "a2"]
    assert ids(member_state="mt") == ["a3"]
    assert ids(entity="example withdrawn") == ["a3"]
    assert ids(entry_id="a2") == ["a2"]
    assert ids(register="casps") == []
    assert ids(change_type="missing") == ["a4"]


def test_change_lei_filter_is_exact_and_skips_records_without_lei():
    def ids(lei):
        return [c["entry_id"] for c in recent_changes(CHANGELOG, lei=lei)["changes"]]

    assert ids("529900example lei0001".replace(" ", "")) == ["a1"]
    assert ids("529900EXAMPLELEI000") == []  # no prefix matching
    assert ids("529900EXAMPLELEI0004") == ["a4"]
    # a2 has this LEI in the snapshot, but its change record carries no `lei`
    # (records from before the observatory added the field), so it never matches.
    assert ids("529900EXAMPLELEI0002") == []


def test_change_paging_reports_next_offset():
    first = recent_changes(CHANGELOG, limit=1)
    assert first["offset"] == 0 and first["next_offset"] == 1
    last = recent_changes(CHANGELOG, limit=1, offset=3)
    assert last["next_offset"] is None
    second = recent_changes(CHANGELOG, limit=1, offset=1)
    assert first["changes"][0] != second["changes"][0]


def test_search_reports_next_offset_and_match_basis():
    result = search_entries(SNAPSHOT, "example issuer gmbh")
    assert result["next_offset"] is None
    assert result["results"][0]["match"] == {"score": 1.0, "basis": "exact_name"}
    assert search_entries(SNAPSHOT, "")["results"][0]["match"] is None
