"""MCP server: EU regulatory grounding tools for AI agents."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, ContentBlock, ToolAnnotations
from pydantic import BaseModel, ValidationError

from eu_reg_mcp import data, integrations, models, register
from eu_reg_mcp.errors import ToolFailure
from eu_reg_mcp.integrations import REVIEW_NOTICE

REGISTER_TOOLS = frozenset(
    {"search_micar_register", "micar_register_summary", "micar_register_changes"}
)


class _Server(FastMCP):
    """FastMCP that returns every tool failure as one structured error shape."""

    async def call_tool(  # type: ignore[override]
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[ContentBlock] | dict[str, Any] | CallToolResult:
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            cause = exc.__cause__
            if isinstance(cause, ToolFailure):
                return cause.to_result()
            if isinstance(cause, ValidationError) and cause.title.endswith("Arguments"):
                return _invalid_arguments(name, cause).to_result()
            raise


def _invalid_arguments(tool: str, error: ValidationError) -> ToolFailure:
    problems = "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )
    return ToolFailure(
        "invalid_input",
        f"Invalid arguments: {problems}",
        hint="See the tool's inputSchema for allowed values.",
        notice=register.NOTICE if tool in REGISTER_TOOLS else REVIEW_NOTICE,
    )


mcp = _Server(
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
REGISTER_SLUGS: tuple[str, ...] = RegisterSlug.__args__  # type: ignore[attr-defined]

# Register tools only read published data; lint/classify are local and pure.
READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
LOCAL_READ_ONLY = ToolAnnotations(
    readOnlyHint=True, idempotentHint=True, openWorldHint=False
)


def _load[T](loader: Callable[[], T]) -> T:
    try:
        return loader()
    except data.DataError as error:
        raise ToolFailure(
            "data_unavailable",
            str(error),
            hint=(
                "The observatory data on raw.githubusercontent.com could not be "
                "fetched and no cached copy exists. Check network access and retry."
            ),
            notice=register.NOTICE,
            extra={"snapshot_date": None, "data_age_days": None, "stale": None},
        ) from error


def _with_warnings(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, "warnings": data.fallback_warnings()}


@mcp.tool(title="Search the MiCAR register", annotations=READ_ONLY)
def search_micar_register(
    query: str,
    register_slug: RegisterSlug = "all",
    member_state: str = "",
    offset: int = 0,
) -> models.SearchResponse:
    """Search the ESMA interim MiCAR register by entity name or LEI.

    query: entity-name substring (case- and accent-insensitive) or an exact LEI.
    Each result carries its entry_id and the ESMA source file; the response
    states the snapshot date, data_age_days and a stale flag.
    register_slug: all | other-wp | emt-wp | art-wp | casps | ncasp.
    member_state: optional two-letter code (DE, IE, MT, ...).
    offset: skip this many matches (results come 25 at a time; see truncated).
    """
    snapshot = _load(data.load_snapshot)
    result = register.search_entries(
        snapshot, query, register_slug, member_state, offset=offset
    )
    return models.SearchResponse.model_validate(_with_warnings(result))


@mcp.tool(title="MiCAR register summary", annotations=READ_ONLY)
def micar_register_summary() -> models.SummaryResponse:
    """Current totals per MiCAR register and white paper format coverage."""
    result = register.summarize(_load(data.load_snapshot))
    return models.SummaryResponse.model_validate(_with_warnings(result))


@mcp.tool(title="MiCAR register changes", annotations=READ_ONLY)
def micar_register_changes(
    limit: int = 50, change_type: ChangeType = "all"
) -> models.ChangesResponse:
    """Recent register movement: new filings, changed entries, removals.

    change_type: all | added | changed | removed.
    Each record says whether the entry is still listed in the latest snapshot.
    """
    result = register.recent_changes(
        _load(data.load_changelog),
        limit,
        change_type,
        snapshot=_load(data.load_snapshot),
    )
    return models.ChangesResponse.model_validate(_with_warnings(result))


@mcp.tool(title="Lint a MiCAR white paper", annotations=LOCAL_READ_ONLY)
def lint_micar_whitepaper(whitepaper_json: str) -> models.LintResponse:
    """Lint a draft MiCAR white paper (JSON) against Annex I-III rules.

    Returns cited candidate findings pending human review. Requires the
    optional `lint` extra; degrades to an install hint when absent.
    """
    return models.LintResponse.model_validate(
        integrations.lint_whitepaper(whitepaper_json)
    )


@mcp.tool(title="Classify an AI system (EU AI Act)", annotations=LOCAL_READ_ONLY)
def classify_eu_ai_act_system(profile_json: str = "") -> models.ClassifyResponse:
    """Classify an AI system's EU AI Act risk tier with pinpoint citations.

    Pass a SystemProfile as JSON; pass an empty string to get the schema.
    Requires the optional `classify` extra; degrades to an install hint.
    """
    return models.ClassifyResponse.model_validate(
        integrations.classify_ai_system(profile_json)
    )


def _print(result: BaseModel | dict[str, Any]) -> None:
    if isinstance(result, BaseModel):
        result = result.model_dump(mode="json")
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
    search.add_argument("--register", default="all", choices=REGISTER_SLUGS)
    search.add_argument("--member-state", default="", help="Two-letter code, e.g. DE.")
    search.add_argument(
        "--offset", type=int, default=0, help="Skip this many matches (25 per page)."
    )
    sub.add_parser("summary", help="Totals per register and white paper formats.")
    changes = sub.add_parser("changes", help="Recent register changes.")
    changes.add_argument("--limit", type=int, default=20)
    changes.add_argument(
        "--type", default="all", choices=["all", "added", "changed", "removed"]
    )
    args = parser.parse_args(argv)

    try:
        _run(args)
    except ToolFailure as failure:
        _print(failure.payload())
        raise SystemExit(1) from failure


def _run(args: argparse.Namespace) -> None:
    if args.command == "search":
        _print(
            search_micar_register(
                args.query, args.register, args.member_state, args.offset
            )
        )
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
