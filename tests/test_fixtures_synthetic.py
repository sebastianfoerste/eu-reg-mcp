"""Guards that keep the fixtures invented and self-consistent.

A row copied from the live register would still pass the other tests, so
these check the fixture data itself.
"""

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

FIXTURES = Path(__file__).parent / "fixtures"

SNAPSHOT = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
CHANGELOG = [
    json.loads(line)
    for line in (FIXTURES / "changelog.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
ENTRIES = [entry for reg in SNAPSHOT["registers"] for entry in reg.get("entries", [])]

# Reserved for documentation and testing (RFC 2606, RFC 6761).
RESERVED_HOST_SUFFIXES = (".example", ".test", ".example.com")


def _lei_number(lei: str) -> int:
    """ISO 7064 MOD 97-10 as used by ISO 17442: letters count as 10 to 35."""
    return int("".join(str(int(char, 36)) for char in lei))


def _lei_check_digits_ok(lei: str) -> bool:
    return len(lei) == 20 and _lei_number(lei) % 97 == 1


def _host(url: str) -> str:
    # Register exports often hold bare domains such as WWW.EXAMPLE.EXAMPLE.
    return (urlsplit(url if "://" in url else f"//{url}").hostname or "").lower()


def test_lei_check_digit_helper_accepts_valid_check_digits():
    base = "529900EXAMPLELEI00"
    check = 98 - _lei_number(base + "00") % 97
    assert _lei_check_digits_ok(f"{base}{check:02d}")


def test_fixture_leis_are_marked_and_fail_the_check_digits():
    leis = [entry["lei"] for entry in ENTRIES if entry.get("lei")]
    assert leis
    for lei in leis:
        assert len(lei) == 20 and "EXAMPLE" in lei, lei
        assert not _lei_check_digits_ok(lei), lei


def test_fixture_urls_use_reserved_hosts():
    urls = [reg["source_url"] for reg in SNAPSHOT["registers"]]
    urls += [entry.get("wp_url", "") for entry in ENTRIES]
    urls += [record.get("wp_url", "") for record in CHANGELOG]
    for url in filter(None, urls):
        assert f".{_host(url)}".endswith(RESERVED_HOST_SUFFIXES), url


def test_no_change_is_dated_after_the_snapshot():
    snapshot_date = date.fromisoformat(SNAPSHOT["snapshot_date"])
    for record in CHANGELOG:
        assert date.fromisoformat(record["snapshot_date"]) <= snapshot_date, record


def test_added_entries_are_listed_and_removed_ones_are_not():
    listed = {entry["entry_id"] for entry in ENTRIES}
    last_change = {
        record["entry_id"]: record["change"]
        for record in CHANGELOG
        if record["change"] in {"added", "removed"}
    }
    assert set(last_change.values()) == {"added", "removed"}
    for entry_id, change in last_change.items():
        assert (entry_id in listed) == (change == "added"), (entry_id, change)
