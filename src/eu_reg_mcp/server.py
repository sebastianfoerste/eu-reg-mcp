"""MCP server: EU regulatory grounding tools for AI agents."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, ContentBlock, ToolAnnotations
from pydantic import BaseModel, ValidationError

from eu_reg_mcp import __version__, data, integrations, models, register
from eu_reg_mcp.errors import ERROR_CODES, ToolFailure
from eu_reg_mcp.integrations import REVIEW_NOTICE

REGISTER_TOOLS = frozenset(
    {"search_micar_register", "micar_register_summary", "micar_register_changes"}
)
ALL_TOOLS = REGISTER_TOOLS | {"lint_micar_whitepaper", "classify_eu_ai_act_system"}
# Register errors answer without a snapshot; they say so instead of omitting it.
NO_SNAPSHOT = {"snapshot_date": None, "data_age_days": None, "stale": None}


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
            if cause is None or name not in ALL_TOOLS:
                raise  # unknown tool and the like: protocol-level as before
            return _unexpected(name, cause).to_result()


def _unexpected(tool: str, error: BaseException) -> ToolFailure:
    """Any other failure still answers in the one error shape, with its notice."""
    message = f"Unexpected {type(error).__name__}: {error}"[:2000]
    if tool in REGISTER_TOOLS:
        return ToolFailure(
            "upstream_failed", message, notice=register.NOTICE, extra=NO_SNAPSHOT
        )
    return ToolFailure("upstream_failed", message, notice=REVIEW_NOTICE)


def _invalid_arguments(tool: str, error: ValidationError) -> ToolFailure:
    problems = "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )
    if tool in REGISTER_TOOLS:
        return ToolFailure(
            "invalid_input",
            f"Invalid arguments: {problems}",
            hint="See the tool's inputSchema for allowed values.",
            notice=register.NOTICE,
            extra=NO_SNAPSHOT,
        )
    return ToolFailure(
        "invalid_input",
        f"Invalid arguments: {problems}",
        hint="See the tool's inputSchema for allowed values.",
        notice=REVIEW_NOTICE,
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


# serverInfo.version would otherwise report the SDK's version.
mcp._mcp_server.version = __version__


RegisterSlug = Literal["all", "other-wp", "emt-wp", "art-wp", "casps", "ncasp"]
ChangeType = Literal["all", "added", "changed", "removed", "missing"]
REGISTER_SLUGS: tuple[str, ...] = RegisterSlug.__args__  # type: ignore[attr-defined]
CHANGE_TYPES: tuple[str, ...] = ChangeType.__args__  # type: ignore[attr-defined]

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
            extra=NO_SNAPSHOT,
        ) from error


SNAPSHOT_ONLY = (data.SNAPSHOT_FILE,)
SNAPSHOT_AND_CHANGELOG = (data.SNAPSHOT_FILE, data.CHANGELOG_FILE)


def _with_warnings(result: dict[str, Any], files: Sequence[str]) -> dict[str, Any]:
    """Add the fallback warnings for the files this answer read, then the
    staleness line when the snapshot is stale or undated; `notice` stays last."""
    body = {key: value for key, value in result.items() if key != "notice"}
    warnings = data.fallback_warnings(files)
    staleness = register.staleness_warning(result)
    if staleness is not None:
        warnings.append(staleness)
    return {**body, "warnings": warnings, "notice": result["notice"]}


@mcp.tool(title="Search the MiCAR register", annotations=READ_ONLY)
def search_micar_register(
    query: str,
    register_slug: RegisterSlug = "all",
    member_state: str = "",
    offset: int = 0,
) -> models.SearchResponse:
    """Search the ESMA interim MiCAR register by entity name or LEI.

    query: name substring (ignores case and accents) or exact LEI. Ranked
    results carry entry_id, ESMA file and match basis. No match:
    similar_names lists close spellings (not matches). member_state: two-letter
    code. 25 per page: offset, next_offset.
    """
    snapshot = _load(data.load_snapshot)
    result = register.search_entries(
        snapshot, query, register_slug, member_state, offset=offset
    )
    return models.SearchResponse.model_validate(_with_warnings(result, SNAPSHOT_ONLY))


@mcp.tool(title="MiCAR register summary", annotations=READ_ONLY)
def micar_register_summary() -> models.SummaryResponse:
    """Totals per MiCAR register and white paper format coverage."""
    result = register.summarize(_load(data.load_snapshot))
    return models.SummaryResponse.model_validate(_with_warnings(result, SNAPSHOT_ONLY))


def _summary_answer() -> models.SummaryResponse:
    result = register.summarize(_resource_load(data.load_snapshot))
    return models.SummaryResponse.model_validate(_with_warnings(result, SNAPSHOT_ONLY))


@mcp.tool(title="MiCAR register changes", annotations=READ_ONLY)
def micar_register_changes(
    limit: int = 50,
    change_type: ChangeType = "all",
    since: date | None = None,
    until: date | None = None,
    register_slug: RegisterSlug = "all",
    member_state: str = "",
    entity: str = "",
    entry_id: str = "",
    lei: str = "",
    offset: int = 0,
) -> models.ChangesResponse:
    """Register changes, newest first: additions, changes, removals.

    Filters: change_type, since/until (snapshot date), register_slug,
    member_state, entity, entry_id, lei. Pages: offset, next_offset.
    still_listed: in latest snapshot. missing: provisional, not a removal.
    """
    result = register.recent_changes(
        _load(data.load_changelog),
        limit,
        change_type,
        snapshot=_load(data.load_snapshot),
        since=since,
        until=until,
        register=register_slug,
        member_state=member_state,
        entity=entity,
        entry_id=entry_id,
        lei=lei,
        offset=offset,
    )
    return models.ChangesResponse.model_validate(
        _with_warnings(result, SNAPSHOT_AND_CHANGELOG)
    )


@mcp.tool(title="Lint a MiCAR white paper", annotations=LOCAL_READ_ONLY)
def lint_micar_whitepaper(whitepaper_json: str) -> models.LintResponse:
    """Lint a draft MiCAR white paper (JSON) against Annex I-III rules.

    Returns cited candidate findings pending human review. Needs the `lint`
    extra.
    """
    return models.LintResponse.model_validate(
        integrations.lint_whitepaper(whitepaper_json)
    )


@mcp.tool(title="Classify an AI system (AI Act)", annotations=LOCAL_READ_ONLY)
def classify_eu_ai_act_system(profile_json: str = "") -> models.ClassifyResponse:
    """Classify an AI system's EU AI Act risk tier with pinpoint citations.

    Pass a SystemProfile as JSON, or an empty string for the schema.
    Needs the `classify` extra.
    """
    return models.ClassifyResponse.model_validate(
        integrations.classify_ai_system(profile_json)
    )


def _json(result: BaseModel | dict[str, Any]) -> str:
    if isinstance(result, BaseModel):
        result = result.model_dump(mode="json")
    return json.dumps(result, ensure_ascii=False, indent=2)


def _resource_error(code: str, message: str) -> ValueError:
    # Resource reads have no isError result, so errors are JSON-RPC errors;
    # the message carries the code and, like every answer, the notice.
    return ValueError(f"{code}: {message} Notice: {register.NOTICE}")


def _resource_load[T](loader: Callable[[], T]) -> T:
    try:
        return _load(loader)
    except ToolFailure as failure:
        raise _resource_error(failure.code, failure.message) from failure


@mcp.resource(
    "eu-reg://about",
    title="About this server",
    description="Version, data sources, network use, error codes and notices.",
    mime_type="application/json",
)
def about() -> str:
    return _json(
        {
            "name": "eu-reg-mcp",
            "version": __version__,
            "data_sources": {
                "snapshot": data.LATEST_URL,
                "changelog": data.CHANGELOG_URL,
            },
            "outbound_hosts": ["raw.githubusercontent.com"],
            "stale_after_days": register.STALE_AFTER_DAYS,
            "extras": {
                "lint": integrations.linter_available(),
                "classify": integrations.classifier_available(),
            },
            "error_codes": list(ERROR_CODES),
            "notices": {"register": register.NOTICE, "review": REVIEW_NOTICE},
        }
    )


@mcp.resource(
    "micar://summary",
    title="MiCAR register summary",
    description="Same answer as micar_register_summary.",
    mime_type="application/json",
)
def summary_resource() -> str:
    return _json(_summary_answer())


@mcp.resource(
    "micar://changes",
    title="Latest MiCAR register changes",
    description="The 50 newest changes; micar_register_changes filters and pages.",
    mime_type="application/json",
)
def changes_resource() -> str:
    result = register.recent_changes(
        _resource_load(data.load_changelog),
        snapshot=_resource_load(data.load_snapshot),
    )
    return _json(
        models.ChangesResponse.model_validate(
            _with_warnings(result, SNAPSHOT_AND_CHANGELOG)
        )
    )


@mcp.resource(
    "micar://entry/{entry_id}",
    title="MiCAR register entry",
    description="One entry by the entry_id that search results carry.",
    mime_type="application/json",
)
def entry_resource(entry_id: str) -> str:
    found = register.get_entry(_resource_load(data.load_snapshot), entry_id)
    if found is None:
        raise _resource_error(
            "invalid_input",
            f"entry_id {entry_id!r} is not in the latest snapshot; it may have "
            "been removed (see micar_register_changes) or never existed.",
        )
    return _json(_with_warnings(found, SNAPSHOT_ONLY))


@mcp.prompt(
    title="Check an entity's MiCAR register status",
    description="Look an entity up and report the register facts with their date.",
)
def check_register_status(entity: str) -> str:
    return (
        f"Look up {entity!r} on the ESMA interim MiCAR register with the "
        "search_micar_register tool (use the LEI if you know it). Report, for "
        "each matching result: the register, entry_id, entity_name, "
        "member_state and esma_source_url, and state the snapshot_date. If "
        "stale is true, say first that the data may be out of date. If nothing "
        "matched, say so plainly; similar_names are not matches and may be "
        "mentioned only as names to check. Report register facts only: do not "
        "assess whether the entity is authorised, compliant or trustworthy. "
        f"End with this notice: {register.NOTICE}"
    )


@mcp.prompt(
    title="Review recent MiCAR register changes",
    description="Summarise register changes since a date, with removals unexplained.",
)
def review_register_changes(since: str = "") -> str:
    window = f" with since={since!r}" if since else ""
    return (
        f"Call micar_register_changes{window} and summarise the changes by "
        "type and register, stating the snapshot_date of the answer and the "
        "snapshot date of each change. For each removal, say that the entry "
        "left the register export and that the register itself does not state "
        "why; do not suggest a reason. A 'missing' record is provisional: the "
        "entry was absent from one export and is recorded as removed only if "
        "the next export also lacks it, so do not report it as a removal. "
        "Use still_listed to say whether an "
        "entry is listed today. Report register facts only, with no legal "
        f"assessment of any entity. End with this notice: {register.NOTICE}"
    )


# Generated parameter titles ("Register Slug") repeat the names; dropping them
# keeps tools/list small. Tool.parameters is the inputSchema FastMCP lists.
for _tool in mcp._tool_manager.list_tools():
    _tool.parameters = models.compact_schema(_tool.parameters)


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
    changes.add_argument("--limit", type=int, default=50)
    changes.add_argument("--type", default="all", choices=CHANGE_TYPES)
    changes.add_argument("--since", type=date.fromisoformat, help="YYYY-MM-DD.")
    changes.add_argument("--until", type=date.fromisoformat, help="YYYY-MM-DD.")
    changes.add_argument("--register", default="all", choices=REGISTER_SLUGS)
    changes.add_argument("--member-state", default="")
    changes.add_argument("--entity", default="", help="Entity-name substring.")
    changes.add_argument("--entry-id", default="")
    changes.add_argument("--lei", default="", help="Exact LEI (newer records only).")
    changes.add_argument("--offset", type=int, default=0)
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
        _print(
            micar_register_changes(
                args.limit,
                args.type,
                args.since,
                args.until,
                args.register,
                args.member_state,
                args.entity,
                args.entry_id,
                args.lei,
                args.offset,
            )
        )
    elif args.transport == "streamable-http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
