"""Resources, the entry template and prompts, read through an MCP client."""

import json
import tomllib
from pathlib import Path

import anyio
import pytest
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import __version__, data, register, server

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(autouse=True)
def offline_data(monkeypatch):
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


def session(action):
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            return await action(client)

    return anyio.run(run)


def read(uri):
    async def action(client):
        result = await client.read_resource(uri)
        return json.loads(result.contents[0].text)

    return session(action)


def test_primitives_are_listed():
    async def action(client):
        return (
            {str(r.uri) for r in (await client.list_resources()).resources},
            {
                t.uriTemplate
                for t in (await client.list_resource_templates()).resourceTemplates
            },
            {p.name for p in (await client.list_prompts()).prompts},
        )

    resources, templates, prompts = session(action)
    assert resources == {"eu-reg://about", "micar://summary", "micar://changes"}
    assert templates == {"micar://entry/{entry_id}"}
    assert prompts == {"check_register_status", "review_register_changes"}


@pytest.mark.parametrize(
    "uri", ["micar://summary", "micar://changes", "micar://entry/a1"]
)
def test_register_resources_are_dated_answers(uri):
    body = read(uri)
    assert body["snapshot_date"] == "2026-07-07"
    assert {"data_age_days", "stale", "warnings"} <= body.keys()
    assert list(body)[-1] == "notice"
    assert body["notice"].startswith(register.NOTICE)


def test_entry_resource_matches_search_result():
    entry = read("micar://entry/a1")["entry"]
    hit = server.search_micar_register("example issuer").model_dump(mode="json")
    hit["results"][0].pop("match")
    assert hit["results"][0] == entry


def test_unknown_entry_is_an_error():
    async def action(client):
        try:
            await client.read_resource("micar://entry/does-not-exist")
        except McpError as error:
            return error
        return None

    error = session(action)
    assert error is not None and "not in the latest snapshot" in str(error)


def test_about_states_version_hosts_and_codes():
    about = read("eu-reg://about")
    assert about["version"] == __version__
    assert about["outbound_hosts"] == ["raw.githubusercontent.com"]
    assert "data_unavailable" in about["error_codes"]
    assert about["notices"]["register"] == register.NOTICE


def test_server_info_reports_this_package_version():
    # serverInfo.version in the initialize result comes from these options.
    options = server.mcp._mcp_server.create_initialization_options()
    assert options.server_version == __version__


def test_version_is_single_sourced():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    assert __version__ == project["project"]["version"]
    assert __version__ in data.USER_AGENT


@pytest.mark.parametrize(
    ("name", "arguments", "must_say"),
    [
        ("check_register_status", {"entity": "Example Issuer"}, "not matches"),
        ("review_register_changes", {"since": "2026-07-01"}, "does not state why"),
        ("review_register_changes", {}, "do not report it as a removal"),
    ],
)
def test_prompts_carry_the_guardrails(name, arguments, must_say):
    async def action(client):
        return await client.get_prompt(name, arguments)

    text = session(action).messages[0].content.text
    assert "snapshot_date" in text
    assert must_say in text
    assert register.NOTICE in text


@pytest.mark.parametrize(
    "uri", ["micar://summary", "micar://changes", "micar://entry/a1"]
)
def test_resource_errors_carry_code_and_notice(monkeypatch, uri):
    def unavailable():
        raise data.DataError("could not load")

    monkeypatch.setattr(data, "load_snapshot", unavailable)

    async def action(client):
        try:
            await client.read_resource(uri)
        except McpError as error:
            return str(error)
        return ""

    message = session(action)
    assert "data_unavailable: could not load" in message
    assert register.NOTICE in message
