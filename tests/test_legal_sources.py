"""`eu-reg://about` lists verified, static identifiers of the instruments."""

import json
import re
from datetime import date

import anyio
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import sources

CELEX = re.compile(r"^[0-9]{5}[A-Z]{1,2}[0-9]{4}$")


def _about():
    async def run():
        async with create_connected_server_and_client_session(
            __import__("eu_reg_mcp.server").server.mcp
        ) as client:
            result = await client.read_resource("eu-reg://about")
            return json.loads(result.contents[0].text)

    return anyio.run(run)


def test_about_lists_verified_legal_sources():
    about = _about()
    listed = about["legal_sources"]
    assert listed == list(sources.LEGAL_SOURCES)
    instruments = " ".join(entry["instrument"] for entry in listed)
    for name in ("2023/1114", "2024/1689", "2026/1744"):
        assert name in instruments
    for entry in listed:
        assert entry["eli"].startswith("http://data.europa.eu/eli/")
        assert CELEX.fullmatch(entry["celex"]), entry["celex"]
        assert entry["provisions"] and entry["instrument"]
        assert date.fromisoformat(entry["verified_on"]) <= date.today()
        if "consolidated_eli" in entry:
            assert entry["consolidated_eli"].startswith("http://data.europa.eu/eli/")


def test_legal_sources_are_static_data_not_outbound_hosts():
    about = _about()
    # The identifiers are documentation; the server still fetches only
    # observatory data.
    assert about["outbound_hosts"] == ["raw.githubusercontent.com"]
    assert "data.europa.eu" not in about["outbound_hosts"]
    assert "eur-lex" not in json.dumps(about["data_sources"])


def test_consolidated_eli_pins_a_date():
    by_celex = {entry["celex"]: entry for entry in sources.LEGAL_SOURCES}
    ai_act = by_celex["32024R1689"]
    assert ai_act["consolidated_eli"].endswith("/2024/1689/2026-07-27")
    assert "consolidated_eli" not in by_celex["32026R1744"]
