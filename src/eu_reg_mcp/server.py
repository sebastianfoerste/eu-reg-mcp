"""MCP server: EU regulatory grounding tools for AI agents."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

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


@mcp.tool()
def search_micar_register(
    query: str, register_slug: str = "all", member_state: str = ""
) -> dict[str, Any]:
    """Search the ESMA interim MiCAR register by entity name or LEI.

    query: entity-name substring (case-insensitive) or an exact LEI.
    register_slug: all | other-wp | emt-wp | art-wp | casps | ncasp.
    member_state: optional two-letter code (DE, IE, MT, ...).
    """
    return register.search_entries(
        data.load_snapshot(), query, register_slug, member_state
    )


@mcp.tool()
def micar_register_summary() -> dict[str, Any]:
    """Current totals per MiCAR register and white paper format coverage."""
    return register.summarize(data.load_snapshot())


@mcp.tool()
def micar_register_changes(limit: int = 50, change_type: str = "all") -> dict[str, Any]:
    """Recent register movement: new filings, changed entries, removals.

    change_type: all | added | changed | removed.
    """
    return register.recent_changes(data.load_changelog(), limit, change_type)


@mcp.tool()
def lint_micar_whitepaper(whitepaper_json: str) -> dict[str, Any]:
    """Lint a draft MiCAR white paper (JSON) against Annex I-III rules.

    Returns cited candidate findings pending human review. Requires the
    optional `lint` extra; degrades to an install hint when absent.
    """
    return integrations.lint_whitepaper(whitepaper_json)


@mcp.tool()
def classify_eu_ai_act_system(profile_json: str = "") -> dict[str, Any]:
    """Classify an AI system's EU AI Act risk tier with pinpoint citations.

    Pass a SystemProfile as JSON; pass an empty string to get the schema.
    Requires the optional `classify` extra; degrades to an install hint.
    """
    return integrations.classify_ai_system(profile_json)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
