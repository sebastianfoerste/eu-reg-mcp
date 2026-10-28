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


def dump(model):
    return model.model_dump(mode="json")


def test_search_tool_end_to_end():
    result = dump(server.search_micar_register("testnet"))
    assert result["total_matches"] == 1


def test_summary_and_changes_tools():
    assert dump(server.micar_register_summary())["snapshot_date"] == "2026-07-07"
    assert dump(server.micar_register_changes(limit=5))["total_changes"] == 4


def test_cli_search_prints_json(capsys):
    server.main(["search", "testnet"])
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


def test_tools_declare_read_only_and_enums():
    import anyio

    tools = {tool.name: tool for tool in anyio.run(server.mcp.list_tools)}
    for tool in tools.values():
        assert tool.annotations is not None and tool.annotations.readOnlyHint is True
    slug = tools["search_micar_register"].inputSchema["properties"]["register_slug"]
    assert "casps" in str(slug)
    change = tools["micar_register_changes"].inputSchema["properties"]["change_type"]
    assert "removed" in str(change)


def test_search_paging():
    first = dump(server.search_micar_register("", offset=0))
    second = dump(server.search_micar_register("", offset=1))
    assert first["total_matches"] == second["total_matches"]
    if first["total_matches"] > 1:
        assert first["results"][1] == second["results"][0]
    assert second["offset"] == 1


def test_changes_tool_states_snapshot_provenance():
    result = dump(server.micar_register_changes(limit=5))
    assert result["snapshot_date"] == "2026-07-07"
    assert {"data_age_days", "stale", "observatory_snapshot"} <= result.keys()
    assert result["notice"]


def test_cli_search_offset(capsys):
    server.main(["search", "", "--offset", "1"])
    out = json.loads(capsys.readouterr().out)
    assert out["offset"] == 1
    assert out["total_matches"] == 3
    assert len(out["results"]) == 2


def test_fixtures_use_only_example_leis():
    # Fixtures are synthetic: fictional names and made-up 529900… LEIs only.
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    leis = [
        entry["lei"]
        for register in snapshot["registers"]
        for entry in register["entries"]
    ]
    assert leis and all(
        lei.startswith("529900") and ("EXAMPLE" in lei or "CASPONE" in lei)
        for lei in leis
    )
