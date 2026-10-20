"""Over-the-wire contract: typed output and one error shape, via an MCP client."""

import json
import sys
import urllib.error
from pathlib import Path

import anyio
import jsonschema
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import data, server
from eu_reg_mcp.errors import ERROR_CODES

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def offline_data(monkeypatch):
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


def call(name, arguments=None):
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            result = await client.call_tool(name, arguments or {})
            return tools[name], result

    return anyio.run(run)


def assert_error(result, code):
    assert result.isError is True
    body = result.structuredContent
    assert body["code"] == code
    assert body["error"]
    assert body["notice"]
    assert json.loads(result.content[0].text) == body
    return body


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("search_micar_register", {"query": "example"}),
        ("micar_register_summary", {}),
        ("micar_register_changes", {"limit": 5}),
    ],
)
def test_register_output_matches_declared_schema(offline_data, name, arguments):
    tool, result = call(name, arguments)
    assert result.isError is False
    assert tool.title
    jsonschema.validate(result.structuredContent, tool.outputSchema)
    # The JSON text block and structuredContent carry the same object.
    assert json.loads(result.content[0].text) == result.structuredContent
    for key in ("snapshot_date", "data_age_days", "stale", "notice"):
        assert key in result.structuredContent
    assert list(result.structuredContent)[-1] == "notice"


def test_output_schemas_are_field_level():
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            return (await client.list_tools()).tools

    for tool in anyio.run(run):
        assert tool.outputSchema is not None
        assert "notice" in tool.outputSchema["properties"], tool.name
        assert "notice" in tool.outputSchema["required"], tool.name


def test_unknown_register_slug_is_invalid_input(offline_data):
    _, result = call("search_micar_register", {"query": "x", "register_slug": "nope"})
    body = assert_error(result, "invalid_input")
    assert "register_slug" in body["error"]


def test_no_data_and_no_cache_is_data_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)

    def offline(url):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(data, "_get", offline)
    data.clear_cache()
    for name in ("search_micar_register", "micar_register_changes"):
        _, result = call(name, {"query": "x"} if name.startswith("search") else {})
        body = assert_error(result, "data_unavailable")
        assert body["snapshot_date"] is None and body["stale"] is None
    data.clear_cache()


def test_cached_fallback_is_a_warning(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)
    (tmp_path / "latest.json").write_bytes((FIXTURES / "latest.json").read_bytes())

    def offline(url):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(data, "_get", offline)
    data.clear_cache()
    _, result = call("search_micar_register", {"query": "example"})
    assert result.isError is False
    assert result.structuredContent["snapshot_date"] == "2026-07-07"
    assert "last good cached copy" in result.structuredContent["warnings"][0]
    data.clear_cache()


def test_missing_extra_is_extra_missing(monkeypatch):
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    monkeypatch.setitem(sys.modules, "micar_linter", None)
    monkeypatch.setitem(sys.modules, "eu_ai_act_classifier.local_api", None)
    _, lint = call("lint_micar_whitepaper", {"whitepaper_json": "{}"})
    assert assert_error(lint, "extra_missing")["available"] is False
    _, classify = call("classify_eu_ai_act_system", {"profile_json": "{}"})
    assert "eu-reg-mcp[classify]" in assert_error(classify, "extra_missing")["hint"]


def test_invalid_json_is_invalid_input(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    _, result = call("lint_micar_whitepaper", {"whitepaper_json": "{not json"})
    assert_error(result, "invalid_input")


def test_error_codes_are_the_documented_set():
    documented = (Path(__file__).parents[1] / "docs" / "tools.md").read_text("utf-8")
    for code in ERROR_CODES:
        assert f"`{code}`" in documented


def test_cli_prints_error_and_exits_nonzero(monkeypatch, capsys):
    def unavailable():
        raise data.DataError("could not load")

    monkeypatch.setattr(data, "load_snapshot", unavailable)
    with pytest.raises(SystemExit) as exit_info:
        server.main(["summary"])
    assert exit_info.value.code == 1
    assert json.loads(capsys.readouterr().out)["code"] == "data_unavailable"


def test_cli_rejects_unknown_register(capsys):
    with pytest.raises(SystemExit) as exit_info:
        server.main(["search", "x", "--register", "nope"])
    assert exit_info.value.code == 2


def test_change_filters_over_mcp(offline_data):
    tool, result = call(
        "micar_register_changes", {"since": "2026-07-14", "member_state": "AT"}
    )
    jsonschema.validate(result.structuredContent, tool.outputSchema)
    assert [c["entry_id"] for c in result.structuredContent["changes"]] == ["a3"]
    assert result.structuredContent["changes"][0]["still_listed"] is False


def test_bad_date_is_invalid_input(offline_data):
    _, result = call("micar_register_changes", {"since": "last week"})
    assert "since" in assert_error(result, "invalid_input")["error"]


def test_cli_changes_filters(offline_data, capsys):
    server.main(["changes", "--since", "2026-07-14", "--entity", "new issuer"])
    out = json.loads(capsys.readouterr().out)
    assert [c["entry_id"] for c in out["changes"]] == ["c9"]


def test_tools_list_input_side_stays_within_budget():
    # Names, titles, descriptions and inputSchemas: what a model reads to pick a
    # tool. 2,904 bytes was the pre-typed-output baseline (2026-10-20).
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            return (await client.list_tools()).tools

    listed = [
        tool.model_dump(by_alias=True, exclude_none=True, mode="json")
        for tool in anyio.run(run)
    ]
    for tool in listed:
        tool.pop("outputSchema", None)
    assert len(json.dumps(listed, separators=(",", ":"))) <= 2904
