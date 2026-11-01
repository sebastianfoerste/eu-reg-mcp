"""Slow tool work runs off the event loop, and concurrent misses fetch once."""

import inspect
import json
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anyio
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import data, server

FIXTURES = Path(__file__).parent / "fixtures"
# The fixture below stubs time.sleep (no retry back-off in tests); the slow
# fakes need the real one.
REAL_SLEEP = time.sleep
TOOLS = [
    "search_micar_register",
    "micar_register_summary",
    "micar_register_changes",
    "lint_micar_whitepaper",
    "classify_eu_ai_act_system",
]


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)
    data.clear_cache()
    yield
    data.clear_cache()


def test_tools_run_through_threaded_wrappers_of_the_sync_functions():
    for name in TOOLS:
        registered = server.mcp._tool_manager.get_tool(name)
        assert registered is not None
        assert inspect.iscoroutinefunction(registered.fn), name
        sync = getattr(server, name)
        assert not inspect.iscoroutinefunction(sync)
        assert registered.fn.__wrapped__ is sync
        assert registered.fn.__doc__ == sync.__doc__
        assert inspect.signature(registered.fn) == inspect.signature(sync)


def test_register_resources_are_threaded_too():
    for name in ("summary_resource", "changes_resource", "entry_resource"):
        assert inspect.iscoroutinefunction(getattr(server, name)), name


def test_slow_fetch_does_not_block_other_requests(isolated, monkeypatch):
    fixture = (FIXTURES / "latest.json").read_bytes()
    changelog = (FIXTURES / "changelog.jsonl").read_bytes()

    def slow_get(url):
        REAL_SLEEP(1.0)
        return changelog if url.endswith("changelog.jsonl") else fixture

    monkeypatch.setattr(data, "_get", slow_get)

    async def run():
        timings = {}
        async with create_connected_server_and_client_session(server.mcp) as client:

            async def summary():
                started = anyio.current_time()
                result = await client.call_tool("micar_register_summary", {})
                timings["tool"] = anyio.current_time() - started
                timings["ok"] = result.isError is False

            async with anyio.create_task_group() as tg:
                tg.start_soon(summary)
                await anyio.sleep(0.1)  # the tool is now sleeping in its thread
                started = anyio.current_time()
                tools = await client.list_tools()
                timings["list"] = anyio.current_time() - started
                timings["names"] = {t.name for t in tools.tools}
        return timings

    timings = anyio.run(run)
    assert timings["ok"] is True
    assert timings["tool"] >= 1.0
    assert timings["list"] < 0.5, timings  # served while the fetch slept
    assert timings["names"] == set(TOOLS)


def test_concurrent_cache_misses_fetch_once(isolated, monkeypatch):
    fixture = (FIXTURES / "latest.json").read_bytes()
    calls = []
    gate = threading.Barrier(4, timeout=5)

    def counted_get(url):
        calls.append(url)
        REAL_SLEEP(0.2)
        return fixture

    monkeypatch.setattr(data, "_get", counted_get)

    def load():
        gate.wait()  # all four threads miss the cache at once
        return data.load_snapshot()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: load(), range(4)))
    assert len(calls) == 1
    assert all(result == json.loads(fixture) for result in results)


def test_lock_does_not_hide_fetch_errors(isolated, monkeypatch):
    def offline(url):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(data, "_get", offline)
    with pytest.raises(data.DataError):
        data.load_snapshot()
    assert not data._lock_for(data.SNAPSHOT_FILE).locked()
