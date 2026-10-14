"""Install smoke test: start eu-reg-mcp over stdio and talk to it as a client.

Usage (everything after ``--`` is the command that launches the server):

    uv run --no-project --with 'mcp>=1.2,<2' python scripts/smoke_list_tools.py -- \
        uvx --refresh --from '.[lint,classify]' eu-reg-mcp

The script connects with the MCP SDK's stdio client, lists the tools and
fails unless exactly the five documented tools are present. It then calls the
two offline tools to prove the extras really are installed in the server's
environment: the classifier must return ``high_risk`` with Art. 26 and
Art. 27 for a synthetic Annex III point 5(b) deployer, and the linter must
run. ``--check-register`` also calls the register summary, which fetches the
observatory's weekly snapshot over the network. Exit status 0 means every
check passed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "search_micar_register",
    "micar_register_summary",
    "micar_register_changes",
    "lint_micar_whitepaper",
    "classify_eu_ai_act_system",
}

BANK_CREDIT_DEPLOYER = {
    "name": "BankCo loan underwriting (smoke test)",
    "roles": ["deployer"],
    "sector": "Banking",
    "annex_iii_area": "III.5.b",
}

SYNTHETIC_DRAFT = {
    "title": "Synthetic smoke-test draft",
    "type": "other",
    "sections": {"summary": "A token."},
}


def _payload(result: Any) -> dict[str, Any]:
    if result.isError:
        text = " ".join(getattr(block, "text", "") for block in result.content)
        raise SystemExit(f"FAIL: tool returned an error: {text[:500]}")
    if result.structuredContent is not None:
        structured = result.structuredContent
        # FastMCP wraps non-object return types as {"result": ...}.
        return structured.get("result", structured)
    return json.loads(result.content[0].text)


async def _call(
    session: ClientSession, name: str, arguments: dict[str, Any], timeout: float
) -> dict[str, Any]:
    with anyio.fail_after(timeout):
        return _payload(await session.call_tool(name, arguments))


async def run(
    command: list[str],
    check_register: bool,
    init_timeout: float,
    call_timeout: float,
) -> int:
    # The SDK passes only a minimal environment to the server by default; pass
    # the caller's environment so proxy and certificate settings reach uvx.
    params = StdioServerParameters(
        command=command[0], args=command[1:], env=dict(os.environ)
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        # First start may build the environment and clone the git extras.
        with anyio.fail_after(init_timeout):
            init = await session.initialize()
        info = init.serverInfo
        print(f"serverInfo: name={info.name} version={info.version}")

        with anyio.fail_after(call_timeout):
            tools = (await session.list_tools()).tools
        names = sorted(tool.name for tool in tools)
        print(f"tools listed: {len(names)}")
        for name in names:
            print(f"  - {name}")
        if set(names) != EXPECTED_TOOLS:
            missing = sorted(EXPECTED_TOOLS - set(names))
            extra = sorted(set(names) - EXPECTED_TOOLS)
            print(f"FAIL: missing={missing} unexpected={extra}")
            return 1

        classify = await _call(
            session,
            "classify_eu_ai_act_system",
            {"profile_json": json.dumps(BANK_CREDIT_DEPLOYER)},
            call_timeout,
        )
        if not classify.get("available"):
            print(f"FAIL: classify extra missing: {classify.get('hint')}")
            return 1
        if "classification" not in classify:
            print(
                f"FAIL: classify returned {classify.get('error')} "
                f"{classify.get('validation_errors')}"
            )
            return 1
        report = classify["classification"]
        articles = sorted(
            {obligation["article"] for obligation in report["obligations"]}
        )
        print(
            f"classify III.5.b deployer: {report['risk_tier']} "
            f"({report['disposition']}), obligations {articles}"
        )
        if report["risk_tier"] != "high_risk" or not {
            "Art. 26 AIA",
            "Art. 27 AIA",
        } <= set(articles):
            print("FAIL: expected high_risk with Art. 26 AIA and Art. 27 AIA")
            return 1

        lint = await _call(
            session,
            "lint_micar_whitepaper",
            {"whitepaper_json": json.dumps(SYNTHETIC_DRAFT)},
            call_timeout,
        )
        if not lint.get("available") or "report" not in lint:
            print(f"FAIL: lint extra missing or failed: {lint}")
            return 1
        summary = lint["report"].get("summary", {})
        print(f"lint synthetic draft: ran, summary {summary}")

        if check_register:
            register = await _call(session, "micar_register_summary", {}, call_timeout)
            totals = {
                entry["register"]: entry["entries"]
                for entry in register.get("registers", [])
            }
            print(
                f"register summary: snapshot_date {register.get('snapshot_date')}, "
                f"entries {totals}"
            )
            if not register.get("snapshot_date"):
                print("FAIL: register summary has no snapshot_date")
                return 1

    print("OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check-register",
        action="store_true",
        help="also call micar_register_summary (needs network access)",
    )
    parser.add_argument(
        "--init-timeout",
        type=float,
        default=600.0,
        help="seconds to wait for the server to start (default: 600)",
    )
    parser.add_argument(
        "--call-timeout",
        type=float,
        default=300.0,
        help="seconds to wait for each list or tool call (default: 300)",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the server command after --")
    return anyio.run(
        run, command, args.check_register, args.init_timeout, args.call_timeout
    )


if __name__ == "__main__":
    sys.exit(main())
