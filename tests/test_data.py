import json
import urllib.error

import pytest

from eu_reg_mcp import data

GOOD = json.dumps({"snapshot_date": "2026-07-07", "registers": []}).encode()


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)
    data.clear_cache()
    yield
    data.clear_cache()


def fake_get(monkeypatch, responses):
    calls = []

    def _get(url):
        calls.append(url)
        item = responses[min(len(calls), len(responses)) - 1]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(data, "_get", _get)
    return calls


def http(code):
    return urllib.error.HTTPError("u", code, "x", {}, None)


def test_retries_transient_errors_then_succeeds(monkeypatch):
    calls = fake_get(monkeypatch, [urllib.error.URLError("down"), http(503), GOOD])
    assert data.load_snapshot()["snapshot_date"] == "2026-07-07"
    assert len(calls) == 3


def test_does_not_retry_404(monkeypatch):
    calls = fake_get(monkeypatch, [http(404)])
    with pytest.raises(data.DataError):
        data.load_snapshot()
    assert len(calls) == 1


def test_gives_up_after_max_attempts(monkeypatch):
    calls = fake_get(monkeypatch, [TimeoutError("slow")])
    with pytest.raises(data.DataError):
        data.load_snapshot()
    assert len(calls) == data.FETCH_ATTEMPTS


def test_backoff_doubles(monkeypatch):
    sleeps = []
    monkeypatch.setattr(data.time, "sleep", sleeps.append)
    fake_get(monkeypatch, [TimeoutError("slow")])
    with pytest.raises(data.DataError):
        data.load_snapshot()
    assert sleeps == [data.BACKOFF_SECONDS, data.BACKOFF_SECONDS * 2]


def test_falls_back_to_disk_cache_when_fetch_fails(monkeypatch):
    fake_get(monkeypatch, [GOOD])
    data.load_snapshot()
    data.clear_cache()  # simulate a fresh process
    fake_get(monkeypatch, [TimeoutError("slow")])
    assert data.load_snapshot()["snapshot_date"] == "2026-07-07"


def test_falls_back_to_memory_when_expired(monkeypatch):
    fake_get(monkeypatch, [GOOD])
    data.load_snapshot()
    monkeypatch.setattr(data, "CACHE_TTL_SECONDS", -1)
    fake_get(monkeypatch, [http(500)])
    assert data.load_snapshot()["registers"] == []


def test_invalid_payload_rejected_and_not_persisted(monkeypatch, tmp_path):
    fake_get(monkeypatch, [b'{"registers": "nope"}'])
    with pytest.raises(data.DataError):
        data.load_snapshot()
    assert not (tmp_path / "latest.json").exists()


def test_invalid_payload_keeps_previous_good_cache(monkeypatch, tmp_path):
    fake_get(monkeypatch, [GOOD])
    data.load_snapshot()
    data.clear_cache()
    fake_get(monkeypatch, [b"<html>captive portal</html>"])
    assert data.load_snapshot()["snapshot_date"] == "2026-07-07"
    assert (tmp_path / "latest.json").read_bytes() == GOOD


def test_corrupt_disk_cache_is_ignored(monkeypatch, tmp_path):
    (tmp_path / "latest.json").write_bytes(b"{truncated")
    fake_get(monkeypatch, [TimeoutError("slow")])
    with pytest.raises(data.DataError):
        data.load_snapshot()


def test_changelog_validation(monkeypatch):
    fake_get(monkeypatch, [b'{"change": "added"}\n[1]\n'])
    with pytest.raises(data.DataError):
        data.load_changelog()
    fake_get(monkeypatch, [b'{"change": "added"}\n\n{"change": "removed"}\n'])
    assert [r["change"] for r in data.load_changelog()] == ["added", "removed"]


def test_atomic_write_leaves_no_temp_files_and_keeps_old_on_failure(
    monkeypatch, tmp_path
):
    target = tmp_path / "f"
    data._write_atomic(target, b"old")

    def boom(*_):
        raise OSError("disk full")

    monkeypatch.setattr(data.os, "replace", boom)
    with pytest.raises(OSError):
        data._write_atomic(target, b"new")
    assert target.read_bytes() == b"old"
    assert [p.name for p in tmp_path.iterdir()] == ["f"]


def test_unwritable_cache_dir_does_not_break_fetch(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(blocker / "sub"))
    fake_get(monkeypatch, [GOOD])
    assert data.load_snapshot()["registers"] == []
