"""Stale or undated register data is said in-band, in `warnings`.

The synthetic fixtures are dated 2026-07-07, so they are always stale; a
fresh-dated copy checks the quiet case. Everything runs through an in-memory
MCP client, the resources and the CLI, which all share `_with_warnings`.
"""

import json
import urllib.error
from datetime import date
from pathlib import Path

import anyio
import jsonschema
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import data, register, server

FIXTURES = Path(__file__).parent / "fixtures"
REGISTER_CALLS = [
    ("search_micar_register", {"query": "example"}),
    ("micar_register_summary", {}),
    ("micar_register_changes", {"limit": 5}),
]


def _fixtures():
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    return snapshot, changelog


def _serve(monkeypatch, snapshot):
    _, changelog = _fixtures()
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


@pytest.fixture
def stale_data(monkeypatch):
    _serve(monkeypatch, _fixtures()[0])


@pytest.fixture
def fresh_data(monkeypatch):
    snapshot, _ = _fixtures()
    _serve(monkeypatch, {**snapshot, "snapshot_date": date.today().isoformat()})


@pytest.fixture
def undated_data(monkeypatch):
    snapshot, _ = _fixtures()
    _serve(monkeypatch, {**snapshot, "snapshot_date": "unknown"})


def call(name, arguments):
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            result = await client.call_tool(name, arguments)
            return tools[name], result

    return anyio.run(run)


def read(uri):
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            result = await client.read_resource(uri)
            return json.loads(result.contents[0].text)

    return anyio.run(run)


def _assert_stale_line(line, snapshot_date="2026-07-07"):
    assert "days old" in line
    assert f"snapshot_date {snapshot_date}" in line
    assert f"stale after {register.STALE_AFTER_DAYS} days" in line
    assert "ESMA register may have changed" in line


@pytest.mark.parametrize(("name", "arguments"), REGISTER_CALLS)
def test_stale_answers_end_with_the_staleness_line(stale_data, name, arguments):
    tool, result = call(name, arguments)
    body = result.structuredContent
    assert result.isError is False and body["stale"] is True
    _assert_stale_line(body["warnings"][-1])
    assert str(body["data_age_days"]) in body["warnings"][-1]
    # The outputSchema is unchanged: warnings was already a list of strings.
    jsonschema.validate(body, tool.outputSchema)
    assert list(body)[-1] == "notice"


@pytest.mark.parametrize(("name", "arguments"), REGISTER_CALLS)
def test_fresh_answers_carry_no_warnings(fresh_data, name, arguments):
    _, result = call(name, arguments)
    assert result.structuredContent["stale"] is False
    assert result.structuredContent["warnings"] == []


@pytest.mark.parametrize(("name", "arguments"), REGISTER_CALLS)
def test_undated_snapshot_says_the_age_is_unknown(undated_data, name, arguments):
    tool, result = call(name, arguments)
    body = result.structuredContent
    assert body["stale"] is None and body["data_age_days"] is None
    line = body["warnings"][-1]
    assert "age is unknown" in line and "snapshot_date unknown" in line
    assert "days old" not in line
    jsonschema.validate(body, tool.outputSchema)


def test_fallback_line_comes_before_the_staleness_line(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)
    (tmp_path / "latest.json").write_bytes((FIXTURES / "latest.json").read_bytes())

    def offline(url):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(data, "_get", offline)
    data.clear_cache()
    try:
        _, result = call("micar_register_summary", {})
    finally:
        data.clear_cache()
    warnings = result.structuredContent["warnings"]
    assert len(warnings) == 2
    assert "last good cached copy" in warnings[0]
    _assert_stale_line(warnings[1])


@pytest.mark.parametrize(
    "uri", ["micar://summary", "micar://changes", "micar://entry/a1"]
)
def test_register_resources_carry_the_staleness_line(stale_data, uri):
    body = read(uri)
    assert body["stale"] is True
    _assert_stale_line(body["warnings"][-1])
    assert list(body)[-1] == "notice"


def test_entry_resource_is_quiet_when_fresh(fresh_data):
    assert read("micar://entry/a1")["warnings"] == []


def test_cli_prints_the_staleness_line(stale_data, capsys):
    server.main(["summary"])
    out = json.loads(capsys.readouterr().out)
    _assert_stale_line(out["warnings"][-1])
    server.main(["search", "example", "--offset", "0"])
    out = json.loads(capsys.readouterr().out)
    _assert_stale_line(out["warnings"][-1])


def test_staleness_warning_helper_is_quiet_when_fresh():
    snapshot, _ = _fixtures()
    fresh = register.summarize(snapshot, today=date(2026, 7, 10))
    assert register.staleness_warning(fresh) is None
    stale = register.summarize(snapshot, today=date(2026, 7, 18))
    assert stale["data_age_days"] == 11
    _assert_stale_line(register.staleness_warning(stale))
    assert "11 days old" in register.staleness_warning(stale)


def test_staleness_wording_lives_in_register_next_to_the_notice():
    # Legal-effect text is reviewed in one place.
    assert "{age}" in register.STALE_WARNING
    assert "{threshold}" in register.AGE_UNKNOWN_WARNING
    assert "not legal advice" in register.NOTICE


def test_live_check_failure_names_date_age_and_threshold(monkeypatch, capsys):
    import importlib.util
    from pathlib import Path as _Path

    spec = importlib.util.spec_from_file_location(
        "live_check", _Path(__file__).parents[1] / "scripts" / "live_check.py"
    )
    live_check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live_check)
    snapshot, changelog = _fixtures()
    monkeypatch.setattr(live_check.data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(live_check.data, "load_changelog", lambda: changelog)
    assert live_check.main() == 1
    out = capsys.readouterr().out
    assert "FAIL: snapshot 2026-07-07 is" in out
    assert f"threshold is {register.STALE_AFTER_DAYS} days" in out
    assert "micar-register-observatory/actions" in out
    monkeypatch.setattr(
        live_check.data, "load_snapshot", lambda: {**snapshot, "snapshot_date": None}
    )
    assert live_check.main() == 1
    assert "missing or unparsable" in capsys.readouterr().out
    monkeypatch.setattr(
        live_check.data,
        "load_snapshot",
        lambda: {**snapshot, "snapshot_date": date.today().isoformat()},
    )
    assert live_check.main() == 0
