"""Register inputs that would otherwise answer with a silent empty set are
rejected as invalid_input (over MCP and on the CLI), and member-state filters
match entries whose published member_state is a country name."""

import json
from pathlib import Path

import anyio
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import __version__, data, register, server

FIXTURES = Path(__file__).parent / "fixtures"

# A synthetic entry published with a country name instead of a code. The LEI
# contains EXAMPLE and fails the ISO 17442 check digits, like the fixtures'.
ISLAND_ENTRY = {
    "entry_id": "c1",
    "register_slug": "casps",
    "authority": "CySEC",
    "member_state": "CYPRUS",
    "entity_name": "Example Island CASP Ltd",
    "lei": "529900EXAMPLECASP002",
    "wp_url": "",
    "last_update": "",
    "format_class": "n/a",
    "row_hash": "h5",
}
ISLAND_CHANGE = {
    "snapshot_date": "2026-07-07",
    "register_slug": "casps",
    "change": "added",
    "entry_id": "c1",
    "entity_name": "Example Island CASP Ltd",
    "member_state": "CYPRUS",
    "wp_url": "",
    "detail": "",
}
BAD_STATES = ["germany", "D", "DEU", "1A"]


@pytest.fixture(autouse=True)
def offline_data(monkeypatch):
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    casps = next(r for r in snapshot["registers"] if r["slug"] == "casps")
    casps["entries"].append(ISLAND_ENTRY)
    changelog.append(ISLAND_CHANGE)
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


def call(name, arguments):
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            return await client.call_tool(name, arguments)

    return anyio.run(run)


def assert_invalid_input(result, field):
    assert result.isError is True
    assert result.structuredContent is None
    body = json.loads(result.content[0].text)
    assert body["code"] == "invalid_input"
    assert field in body["error"]
    assert body["hint"]
    assert body["snapshot_date"] is None
    assert body["data_age_days"] is None
    assert body["stale"] is None
    assert list(body)[-1] == "notice" and body["notice"] == register.NOTICE
    return body


@pytest.mark.parametrize("state", BAD_STATES)
@pytest.mark.parametrize("tool", ["search_micar_register", "micar_register_changes"])
def test_non_two_letter_member_state_is_invalid_input(tool, state):
    arguments = {"member_state": state}
    if tool == "search_micar_register":
        arguments["query"] = "bank"
    body = assert_invalid_input(call(tool, arguments), "member_state")
    assert body["hint"] == server.MEMBER_STATE_HINT
    assert "two-letter" in body["hint"]


def test_validation_happens_before_any_fetch(monkeypatch):
    def unavailable():
        raise data.DataError("should not be called")

    monkeypatch.setattr(data, "load_snapshot", unavailable)
    monkeypatch.setattr(data, "load_changelog", unavailable)
    assert_invalid_input(
        call("search_micar_register", {"query": "x", "member_state": "germany"}),
        "member_state",
    )
    assert_invalid_input(call("micar_register_changes", {"limit": 0}), "limit")


@pytest.mark.parametrize("state", ["de", "DE", "", " DE "])
def test_codes_and_empty_still_answer(state):
    result = call("search_micar_register", {"query": "example", "member_state": state})
    assert result.isError is False
    expected = 1 if state.strip() else 3
    assert result.structuredContent["total_matches"] == expected
    changes = call("micar_register_changes", {"member_state": state})
    assert changes.isError is False


@pytest.mark.parametrize("state", ["CY", "cy"])
def test_country_name_in_data_is_found_by_its_code(state):
    search = call("search_micar_register", {"query": "", "member_state": state})
    assert search.isError is False
    assert search.structuredContent["total_matches"] == 1
    hit = search.structuredContent["results"][0]
    assert hit["entry_id"] == "c1"
    assert hit["member_state"] == "CYPRUS"  # shown as published
    changes = call("micar_register_changes", {"member_state": state})
    assert [c["entry_id"] for c in changes.structuredContent["changes"]] == ["c1"]


def test_name_as_filter_value_is_rejected_not_mapped():
    # The map applies to published data, not to the caller's filter: a reader
    # should learn the code, as the hint says.
    body = assert_invalid_input(
        call("search_micar_register", {"query": "", "member_state": "cyprus"}),
        "member_state",
    )
    assert body["hint"] == server.MEMBER_STATE_HINT


def test_negative_offset_is_invalid_input():
    assert_invalid_input(
        call("search_micar_register", {"query": "example", "offset": -1}), "offset"
    )
    assert_invalid_input(call("micar_register_changes", {"offset": -1}), "offset")


def test_limit_below_one_is_invalid_input_and_cap_still_applies():
    assert_invalid_input(call("micar_register_changes", {"limit": 0}), "limit")
    assert_invalid_input(call("micar_register_changes", {"limit": -5}), "limit")
    assert call("micar_register_changes", {"limit": 1}).isError is False
    big = call("micar_register_changes", {"limit": 500})
    assert big.isError is False
    assert len(big.structuredContent["changes"]) <= register.MAX_CHANGES


def test_pure_filters_compare_codes_on_both_sides():
    snapshot = data.load_snapshot()
    assert (
        register.search_entries(snapshot, "", member_state="CY")["total_matches"] == 1
    )
    assert (
        register.search_entries(snapshot, "", member_state="FR")["total_matches"] == 1
    )
    assert register._state_code(" cyprus ") == "CY"
    assert register._state_code("GR") == "GR"
    assert register._state_code(None) == ""


def test_cli_version_prints_the_version_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as exit_info:
        server.main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"eu-reg-mcp {__version__}"


@pytest.mark.parametrize(
    ("argv", "field"),
    [
        (["search", "bank", "--member-state", "germany"], "member_state"),
        (["search", "bank", "--offset", "-1"], "offset"),
        (["changes", "--limit", "0"], "limit"),
        (["changes", "--member-state", "DEU"], "member_state"),
    ],
)
def test_cli_rejects_bad_inputs_with_the_error_json(capsys, argv, field):
    with pytest.raises(SystemExit) as exit_info:
        server.main(argv)
    assert exit_info.value.code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["code"] == "invalid_input"
    assert field in out["error"]
    assert out["hint"]
