"""Typed tool responses: the field-level outputSchema each tool declares.

Every model mirrors the dict the query functions already return, so the JSON
text block and structuredContent carry the same keys in the same order. The
schemas are compacted (no generated titles or null defaults) to keep
`tools/list` small.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)


def _compact(node: Any) -> Any:
    """Drop generated titles and null defaults; fold `X | None` into a type list."""
    if isinstance(node, list):
        return [_compact(item) for item in node]
    if not isinstance(node, dict):
        return node
    out: dict[str, Any] = {}
    for key, value in node.items():
        if key == "title" and isinstance(value, str):
            continue
        if key == "default" and value is None:
            continue
        if key in ("properties", "$defs"):
            out[key] = {name: _compact(schema) for name, schema in value.items()}
        else:
            out[key] = _compact(value)
    variants = out.get("anyOf")
    if (
        isinstance(variants, list)
        and variants
        and all(set(v) == {"type"} and isinstance(v["type"], str) for v in variants)
    ):
        out.pop("anyOf")
        out["type"] = [v["type"] for v in variants]
    return out


class _Model(BaseModel):
    # `register` would shadow a BaseModel attribute, so it is aliased.
    model_config = ConfigDict(serialize_by_alias=True, validate_by_name=True)

    # Optional keys that are left out of the response when unset.
    _omit_if_none: ClassVar[frozenset[str]] = frozenset()

    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        result: dict[str, Any] = _compact(super().model_json_schema(*args, **kwargs))
        return result

    @model_serializer(mode="wrap")
    def _drop_unset(self, handler: SerializerFunctionWrapHandler) -> Any:
        data = handler(self)
        for key in self._omit_if_none:
            if data.get(key) is None:
                data.pop(key, None)
        return data


class Provenance(_Model):
    snapshot_date: str | None
    data_age_days: int | None
    stale: bool | None
    observatory_snapshot: str


class RegisterEntry(_Model):
    register_: str | None = Field(alias="register")
    entry_id: str | None
    entity_name: str | None
    lei: str | None
    member_state: str | None
    authority: str | None
    whitepaper_url: str | None
    format_class: str | None
    register_last_update: str | None
    esma_source_url: str | None


class SearchResponse(Provenance):
    total_matches: int
    offset: int
    results: list[RegisterEntry]
    truncated: bool
    warnings: list[str] = Field(default_factory=list)
    notice: str


class RegisterTotal(_Model):
    register_: str | None = Field(alias="register")
    title: str | None
    entries: int
    fetched: bool | None
    esma_source_url: str | None


class SummaryResponse(Provenance):
    registers: list[RegisterTotal]
    whitepaper_format_coverage: dict[str, int]
    warnings: list[str] = Field(default_factory=list)
    notice: str


class ChangeRecord(_Model):
    # Changelog records pass through as published; new observatory fields stay.
    model_config = ConfigDict(
        extra="allow", serialize_by_alias=True, validate_by_name=True
    )

    snapshot_date: str | None = None
    register_slug: str | None = None
    change: str
    entry_id: str | None = None
    entity_name: str | None = None
    member_state: str | None = None
    wp_url: str | None = None
    detail: str | None = None
    still_listed: bool | None = None

    _omit_if_none = frozenset({"still_listed"})


class ChangesResponse(Provenance):
    total_changes: int
    changes: list[ChangeRecord]
    changelog_source: str
    warnings: list[str] = Field(default_factory=list)
    notice: str


class LintResponse(_Model):
    available: bool
    report: dict[str, Any]
    notice: str


class ClassifyResponse(_Model):
    available: bool
    classification: dict[str, Any] | None = None
    profile_schema: dict[str, Any] | None = None
    notice: str

    _omit_if_none = frozenset({"classification", "profile_schema"})
