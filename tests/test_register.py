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
