"""One error model for every tool: an isError result with a stable code.

A tool raises ToolFailure; the server turns it into a CallToolResult with
`isError: true`, the same JSON in a text block and in structuredContent, and
the response's `notice`. Clients skip outputSchema validation on errors.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from mcp.types import CallToolResult, TextContent

ErrorCode = Literal[
    "data_unavailable",  # register data could not be loaded and no cache exists
    "extra_missing",  # the lint or classify extra is not installed
    "invalid_input",  # arguments failed validation or JSON did not parse
    "upstream_failed",  # the linter or classifier failed or gave unusable output
    "timeout",  # the linter did not finish in time
]

ERROR_CODES: tuple[str, ...] = ErrorCode.__args__  # type: ignore[attr-defined]


class ToolFailure(Exception):
    """A tool could not answer; carries what the caller needs to recover."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        notice: str,
        hint: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.notice = notice
        self.extra = extra or {}

    def payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {**self.extra, "code": self.code, "error": self.message}
        if self.hint is not None:
            body["hint"] = self.hint
        body["notice"] = self.notice
        return body

    def to_result(self) -> CallToolResult:
        body = self.payload()
        text = json.dumps(body, ensure_ascii=False, indent=2)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=body,
            isError=True,
        )
