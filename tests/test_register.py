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
    result = search_entries(SNAPSHOT, "skygate")
    assert result["total_matches"] == 1
    assert result["results"][0]["entity_name"] == "SKYGATE Network GmbH"
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
    assert result["total_changes"] == 2
    assert result["changes"][0]["change"] in {"added", "removed"}
    removed = recent_changes(CHANGELOG, change_type="removed")
    assert removed["total_changes"] == 1
    assert removed["changes"][0]["entity_name"] == "SKYGATE Network GmbH"


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
                        "entity_name": "Société Générale-Forge",
                    }
                ],
            }
        ],
    }
    assert search_entries(accented, "SOCIETE generale")["total_matches"] == 1
    assert search_entries(accented, "société")["total_matches"] == 1


def test_search_results_are_verifiable():
    from datetime import date

    result = search_entries(SNAPSHOT, "skygate", today=date(2026, 7, 10))
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
    assert "still_listed" not in recent_changes(CHANGELOG)["changes"][0]
