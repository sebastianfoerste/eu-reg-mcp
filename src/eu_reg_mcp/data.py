"""Fetch and cache the observatory's published register data.

The MiCAR Register Observatory commits its normalized snapshot and changelog
to GitHub; this module reads those raw files so every MCP client sees the
same weekly, review-gated dataset without touching ESMA directly.
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

OBSERVATORY_RAW = (
    "https://raw.githubusercontent.com/sebastianfoerste/micar-register-observatory/main"
)
LATEST_URL = f"{OBSERVATORY_RAW}/data/latest.json"
CHANGELOG_URL = f"{OBSERVATORY_RAW}/data/changelog.jsonl"

USER_AGENT = "eu-reg-mcp/0.1 (+https://github.com/sebastianfoerste/eu-reg-mcp)"

CACHE_TTL_SECONDS = 3600  # register moves weekly; an hour is generous

_cache: dict[str, tuple[float, Any]] = {}


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _cached(key: str, url: str, parse: Any) -> Any:
    now = time.monotonic()
    hit = _cache.get(key)
    if hit is not None and now - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    value = parse(_get(url))
    _cache[key] = (now, value)
    return value


def load_snapshot() -> dict[str, Any]:
    return _cached("latest", LATEST_URL, lambda raw: json.loads(raw.decode("utf-8")))


def load_changelog() -> list[dict[str, Any]]:
    def parse(raw: bytes) -> list[dict[str, Any]]:
        return [
            json.loads(line)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]

    return _cached("changelog", CHANGELOG_URL, parse)


def clear_cache() -> None:
    _cache.clear()
