"""MCP server: EU regulatory grounding tools for AI agents."""

from __future__ import annotations

import argparse
import json
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from eu_reg_mcp import data, integrations, register

mcp = FastMCP(
    "eu-reg-mcp",
    instructions=(
        "Regulatory grounding tools over public EU sources: the ESMA interim "
        "MiCAR register (weekly snapshots via the MiCAR Register Observatory), "
        "plus optional deterministic white paper linting (MiCAR Annex I-III) "
        "and EU AI Act risk-tier classification. All outputs are factual "
        "observations or candidate flags pending human legal review — never "
        "legal advice. Cite the register snapshot date when answering."
    ),
)


RegisterSlug = Literal["all", "other-wp", "emt-wp", "art-wp", "casps", "ncasp"]
ChangeType = Literal["all", "added", "changed", "removed"]

# Register tools only read published data; lint/classify are local and pure.
READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
LOCAL_READ_ONLY = ToolAnnotations(
    readOnlyHint=True, idempotentHint=True, openWorldHint=False
)


@mcp.tool(annotations=READ_ONLY)
def search_micar_register(
    query: str,
    register_slug: RegisterSlug = "all",
    member_state: str = "",
    offset: int = 0,
) -> dict[str, Any]:
    """Search the ESMA interim MiCAR register by entity name or LEI.

    query: entity-name substring (case- and accent-insensitive) or an exact LEI.
    Each result carries its entry_id and the ESMA source file; the response
    states the snapshot date, data_age_days and a stale flag.
    register_slug: all | other-wp | emt-wp | art-wp | casps | ncasp.
    member_state: optional two-letter code (DE, IE, MT, ...).
    offset: skip this many matches (results come 25 at a time; see truncated).
    """
    return register.search_entries(
        data.load_snapshot(), query, register_slug, member_state, offset=offset
    )


@mcp.tool(annotations=READ_ONLY)
def micar_register_summary() -> dict[str, Any]:
    """Current totals per MiCAR register and white paper format coverage."""
    return register.summarize(data.load_snapshot())


@mcp.tool(annotations=READ_ONLY)
def micar_register_changes(
    limit: int = 50, change_type: ChangeType = "all"
) -> dict[str, Any]:
    """Recent register movement: new filings, changed entries, removals.

    change_type: all | added | changed | removed.
    Each record says whether the entry is still listed in the latest snapshot.
    """
    return register.recent_changes(
        data.load_changelog(), limit, change_type, snapshot=data.load_snapshot()
    )


@mcp.tool(annotations=LOCAL_READ_ONLY)
def lint_micar_whitepaper(whitepaper_json: str) -> dict[str, Any]:
    """Lint a draft MiCAR white paper (JSON) against Annex I-III rules.

    Returns cited candidate findings pending human review. Requires the
    optional `lint` extra; degrades to an install hint when absent.
    """
    return integrations.lint_whitepaper(whitepaper_json)


@mcp.tool(annotations=LOCAL_READ_ONLY)
def classify_eu_ai_act_system(profile_json: str = "") -> dict[str, Any]:
    """Classify an AI system's EU AI Act risk tier with pinpoint citations.

    Pass a SystemProfile as JSON; pass an empty string to get the schema.
    Requires the optional `classify` extra; degrades to an install hint.
    """
    return integrations.classify_ai_system(profile_json)


def _print(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="eu-reg-mcp",
        description=(
            "MCP server for EU regulatory grounding. Without a subcommand it "
            "serves MCP (stdio by default); the subcommands query the MiCAR "
            "register directly and print JSON."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport when serving (default: stdio).",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="HTTP port (default: 8000)."
    )
    sub = parser.add_subparsers(dest="command")
    search = sub.add_parser("search", help="Search the MiCAR register by name or LEI.")
    search.add_argument("query")
    search.add_argument(
        "--register",
        default="all",
        help="all | other-wp | emt-wp | art-wp | casps | ncasp",
    )
    search.add_argument("--member-state", default="", help="Two-letter code, e.g. DE.")
    sub.add_parser("summary", help="Totals per register and white paper formats.")
    changes = sub.add_parser("changes", help="Recent register changes.")
    changes.add_argument("--limit", type=int, default=20)
    changes.add_argument(
        "--type", default="all", choices=["all", "added", "changed", "removed"]
    )
    args = parser.parse_args(argv)

    if args.command == "search":
        _print(search_micar_register(args.query, args.register, args.member_state))
    elif args.command == "summary":
        _print(micar_register_summary())
    elif args.command == "changes":
        _print(micar_register_changes(args.limit, args.type))
    elif args.transport == "streamable-http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
