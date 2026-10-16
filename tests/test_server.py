import json
from pathlib import Path

import pytest

from eu_reg_mcp import data, server

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def offline_data(monkeypatch):
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


def test_tools_are_registered():
    import anyio

    tools = anyio.run(server.mcp.list_tools)
    names = {tool.name for tool in tools}
    assert names == {
        "search_micar_register",
        "micar_register_summary",
        "micar_register_changes",
        "lint_micar_whitepaper",
        "classify_eu_ai_act_system",
    }


def test_search_tool_end_to_end():
    result = server.search_micar_register("skygate")
    assert result["total_matches"] == 1


def test_summary_and_changes_tools():
    assert server.micar_register_summary()["snapshot_date"] == "2026-07-07"
    assert server.micar_register_changes(limit=5)["total_changes"] == 2


def test_cli_search_prints_json(capsys):
    server.main(["search", "skygate"])
    out = json.loads(capsys.readouterr().out)
    assert out["total_matches"] >= 1
    assert out["results"][0]["entry_id"]


def test_cli_summary_and_changes(capsys):
    server.main(["summary"])
    assert "registers" in json.loads(capsys.readouterr().out)
    server.main(["changes", "--type", "removed", "--limit", "5"])
    out = json.loads(capsys.readouterr().out)
    assert all(c["change"] == "removed" for c in out["changes"])
    assert all("still_listed" in c for c in out["changes"])


def test_http_transport_is_configured(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        server.mcp, "run", lambda transport="stdio": calls.update(t=transport)
    )
    server.main(["--transport", "streamable-http", "--port", "8123"])
    assert calls["t"] == "streamable-http"
    assert server.mcp.settings.port == 8123


def test_default_serves_stdio(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        server.mcp, "run", lambda transport="stdio": calls.update(t=transport)
    )
    server.main([])
    assert calls["t"] == "stdio"
