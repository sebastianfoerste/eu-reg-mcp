"""Fetch and cache the observatory's published register data.

The MiCAR Register Observatory commits its normalized snapshot and changelog
to GitHub; this module reads those raw files so every MCP client sees the
same weekly, review-gated dataset without touching ESMA directly.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from eu_reg_mcp import __version__

OBSERVATORY_RAW = (
    "https://raw.githubusercontent.com/sebastianfoerste/micar-register-observatory/main"
)
LATEST_URL = f"{OBSERVATORY_RAW}/data/latest.json"
CHANGELOG_URL = f"{OBSERVATORY_RAW}/data/changelog.jsonl"

USER_AGENT = (
    f"eu-reg-mcp/{__version__} (+https://github.com/sebastianfoerste/eu-reg-mcp)"
)

CACHE_TTL_SECONDS = 3600  # register moves weekly; an hour is generous
FETCH_ATTEMPTS = 3
BACKOFF_SECONDS = 1.0  # doubled after each failed attempt
FETCH_TIMEOUT_SECONDS = 30

log = logging.getLogger(__name__)

_cache: dict[str, tuple[float, Any]] = {}
# Files currently served from the last good copy after a failed refresh.
_fallbacks: dict[str, str] = {}


class DataError(RuntimeError):
    """Register data could not be fetched and no cached copy exists."""


def cache_dir() -> Path:
    override = os.environ.get("EU_REG_MCP_CACHE_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "eu-reg-mcp"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        return response.read()


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or exc.code >= 500
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError))


def _get_with_retry(url: str) -> bytes:
    delay = BACKOFF_SECONDS
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            return _get(url)
        except Exception as exc:
            if attempt == FETCH_ATTEMPTS or not _retryable(exc):
                raise
            log.warning("fetch of %s failed (%s); retrying in %.1fs", url, exc, delay)
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def _write_atomic(path: Path, raw: bytes) -> None:
    """Write via a temp file in the same directory, then rename into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _validate_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("snapshot must be a JSON object")
    registers = value.get("registers")
    if not isinstance(registers, list):
        raise ValueError("snapshot.registers must be a list")
    for register in registers:
        if not isinstance(register, dict):
            raise ValueError("each register must be an object")
        entries = register.get("entries", [])
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise ValueError("register.entries must be a list of objects")
    return value


def _parse_snapshot(raw: bytes) -> dict[str, Any]:
    return _validate_snapshot(json.loads(raw.decode("utf-8")))


def _parse_changelog(raw: bytes) -> list[dict[str, Any]]:
    records = [
        json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()
    ]
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("change"), str):
            raise ValueError("changelog records must be objects with a 'change' field")
    return records


def _cached(key: str, url: str, parse: Callable[[bytes], Any]) -> Any:
    now = time.monotonic()
    hit = _cache.get(key)
    if hit is not None and now - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    path = cache_dir() / key
    try:
        raw = _get_with_retry(url)
        value = parse(raw)  # validate before anything is persisted
    except (OSError, ValueError) as exc:  # URLError/timeouts are OSErrors
        stale = _stale(key, path, parse, hit)
        if stale is None:
            raise DataError(f"could not load {url}: {exc}") from exc
        log.warning("using stale cached %s after fetch failure: %s", key, exc)
        _fallbacks[key] = str(exc)
        return stale
    try:
        _write_atomic(path, raw)
    except OSError as exc:
        log.warning("could not write cache file %s: %s", path, exc)
    _cache[key] = (now, value)
    _fallbacks.pop(key, None)
    return value


def _stale(
    key: str,
    path: Path,
    parse: Callable[[bytes], Any],
    hit: tuple[float, Any] | None,
) -> Any | None:
    if hit is not None:
        return hit[1]
    try:
        return parse(path.read_bytes())
    except (OSError, ValueError):
        return None


def load_snapshot() -> dict[str, Any]:
    return _cached(SNAPSHOT_FILE, LATEST_URL, _parse_snapshot)


def load_changelog() -> list[dict[str, Any]]:
    return _cached(CHANGELOG_FILE, CHANGELOG_URL, _parse_changelog)


SNAPSHOT_FILE = "latest.json"
CHANGELOG_FILE = "changelog.jsonl"


def fallback_warnings(keys: Iterable[str]) -> list[str]:
    """One line per data file, among those an answer read, that is served from
    the last good copy after a failed refresh."""
    return [
        f"Refreshing {key} failed ({_fallbacks[key]}); this answer uses the last "
        f"good cached copy of {key}, which may be older than the snapshot_date "
        "shown."
        for key in sorted(set(keys))
        if key in _fallbacks
    ]


def clear_cache() -> None:
    """Drop the in-memory cache (the on-disk stale fallback is kept)."""
    _cache.clear()
    _fallbacks.clear()
