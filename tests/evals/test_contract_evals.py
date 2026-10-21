"""Contract evals: golden tasks in tasks/*.json, run through an MCP client.

Each task sets up a fictional data state, makes one tool call, resource read
or prompt request, and checks the answer's contract: dates, notice, error
code, and no compliance-style keys. No model, key or network is involved;
the client validates structuredContent against each tool's outputSchema.
"""

import importlib.util
import json
import subprocess
import sys
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any

import anyio
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from eu_reg_mcp import data, integrations, register, server

HERE = Path(__file__).parent
FIXTURES = HERE.parent / "fixtures"
TASKS = sorted(HERE.glob("tasks/*.json"))

# Keys that would turn register facts or rule output into a verdict.
FORBIDDEN_KEYS = {
    "compliance_status",
    "compliance_score",
    "risk_score",
    "risk_rating",
    "trust_score",
    "rating",
    "removal_reason",
}
MISSING = object()


def _fixtures() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    snapshot = json.loads((FIXTURES / "latest.json").read_text(encoding="utf-8"))
    changelog = [
        json.loads(line)
        for line in (FIXTURES / "changelog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    return snapshot, changelog


def _offline(monkeypatch, tmp_path):
    monkeypatch.setenv("EU_REG_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(data.time, "sleep", lambda _: None)

    def no_network(url):
        raise urllib.error.URLError("eval: offline")

    monkeypatch.setattr(data, "_get", no_network)
    data.clear_cache()


def _setup(name: str, monkeypatch, tmp_path) -> None:
    snapshot, changelog = _fixtures()
    if name == "offline":
        _offline(monkeypatch, tmp_path)
        return
    if name == "fallback":
        _offline(monkeypatch, tmp_path)
        (tmp_path / "latest.json").write_bytes((FIXTURES / "latest.json").read_bytes())
        return
    if name == "fresh":
        snapshot = {**snapshot, "snapshot_date": date.today().isoformat()}
    if name == "no_extras":
        monkeypatch.setattr(integrations.shutil, "which", lambda _: None)
        monkeypatch.setitem(sys.modules, "micar_linter", None)
        monkeypatch.setitem(sys.modules, "eu_ai_act_classifier.local_api", None)
    if name == "lint_bad_output":
        monkeypatch.setattr(integrations.shutil, "which", lambda _: "/bin/micar-lint")
        monkeypatch.setattr(
            integrations.subprocess,
            "run",
            lambda *_a, **_k: subprocess.CompletedProcess(
                [], 1, "Traceback: not JSON", ""
            ),
        )
    if name == "lint_timeout":
        monkeypatch.setattr(integrations.shutil, "which", lambda _: "/bin/micar-lint")

        def hang(*_args, **kwargs):
            raise subprocess.TimeoutExpired("micar-lint", kwargs["timeout"])

        monkeypatch.setattr(integrations.subprocess, "run", hang)
    monkeypatch.setattr(data, "load_snapshot", lambda: snapshot)
    monkeypatch.setattr(data, "load_changelog", lambda: changelog)


def _get(body: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(body, list) and part.isdigit() and int(part) < len(body):
            body = body[int(part)]
        elif isinstance(body, dict) and part in body:
            body = body[part]
        else:
            return MISSING
    return body


def _keys(body: Any) -> set[str]:
    if isinstance(body, dict):
        return set(body) | {k for value in body.values() for k in _keys(value)}
    if isinstance(body, list):
        return {k for item in body for k in _keys(item)}
    return set()


def _run(call: dict[str, Any]) -> tuple[Any, bool | None]:
    async def go():
        async with create_connected_server_and_client_session(server.mcp) as client:
            if "tool" in call:
                result = await client.call_tool(call["tool"], call["arguments"])
                text = json.loads(result.content[0].text)
                if result.isError:
                    # Error JSON goes in the text block only (see errors.py).
                    assert result.structuredContent is None
                    return text, True
                assert text == result.structuredContent, "text and structured differ"
                return result.structuredContent, result.isError
            if "resource" in call:
                result = await client.read_resource(call["resource"])
                return json.loads(result.contents[0].text), None
            prompt = await client.get_prompt(call["prompt"], call["arguments"])
            return {"text": prompt.messages[0].content.text}, None

    return anyio.run(go)


def _passthrough(
    kind: str, arguments: dict[str, Any], body: dict[str, Any], workdir: Path
) -> None:
    """The sibling's output must arrive byte-for-byte as the sibling made it."""
    if kind == "classify":
        from eu_ai_act_classifier.local_api import classify_payload

        direct = classify_payload(json.loads(arguments["profile_json"]))
        assert body["classification"] == json.loads(json.dumps(direct))
    if kind == "lint":
        command = integrations._linter_command()
        assert command is not None
        draft = workdir / "draft.json"
        draft.write_text(arguments["whitepaper_json"], encoding="utf-8")
        out = subprocess.run(
            [*command, str(draft), "--json"],
            capture_output=True,
            text=True,
            timeout=integrations.LINT_TIMEOUT_SECONDS,
        )
        assert body["report"] == json.loads(out.stdout)


def _installed(extra: str) -> bool:
    if extra == "lint":
        return integrations.linter_available()
    return importlib.util.find_spec("eu_ai_act_classifier") is not None


def test_suite_size():
    assert len(TASKS) >= 15


@pytest.mark.parametrize("path", TASKS, ids=[p.stem for p in TASKS])
def test_task(path, monkeypatch, tmp_path):
    task = json.loads(path.read_text(encoding="utf-8"))
    expect = task["expect"]
    if "requires" in expect and not _installed(expect["requires"]):
        pytest.skip(f"needs the {expect['requires']} extra")
    _setup(task["setup"], monkeypatch, tmp_path)
    try:
        body, is_error = _run(task["call"])
    finally:
        data.clear_cache()

    if "isError" in expect:
        assert is_error is expect["isError"]
    for key, value in expect.get("equals", {}).items():
        assert _get(body, key) == value, key
    for key in expect.get("present", []):
        assert _get(body, key) is not MISSING, key
    for key, needle in expect.get("contains", {}).items():
        assert needle in _get(body, key), key
    for key, floor in expect.get("greater", {}).items():
        assert _get(body, key) > floor, key
    if expect.get("contains_notice"):
        assert register.NOTICE in body["text"]
    if "passthrough" in expect:
        _passthrough(expect["passthrough"], task["call"]["arguments"], body, tmp_path)

    if "text" not in body:  # tool and resource answers, not prompt text
        assert body["notice"], "every answer keeps its notice"
        assert list(body)[-1] == "notice", "notice is the last key"
        if "tool" in task["call"] and task["call"]["tool"] in server.REGISTER_TOOLS:
            assert {"snapshot_date", "data_age_days", "stale"} <= body.keys()
        if "resource" in task["call"]:
            assert {"snapshot_date", "data_age_days", "stale"} <= body.keys()
    forbidden = _keys(body) & FORBIDDEN_KEYS
    if expect.get("passthrough"):
        # Sibling output is theirs to shape; only our envelope is checked.
        forbidden = set(body) & FORBIDDEN_KEYS
    assert not forbidden, forbidden
