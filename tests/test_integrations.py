import json
import sys

import pytest

from eu_reg_mcp.integrations import classify_ai_system, lint_whitepaper

UVX_COMMAND = 'uvx --from "eu-reg-mcp[lint,classify]" eu-reg-mcp'


def write_fake_linter(directory, label):
    # Stands in for the micar-lint console script and reports where it was found.
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / "micar-lint"
    script.write_text(f"#!/bin/sh\necho '{json.dumps({'found': label})}'\n")
    script.chmod(0o755)


def write_fake_linter_package(directory, label):
    package = directory / "micar_linter"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "__main__.py").write_text(
        "import json, sys\n"
        f"print(json.dumps({{'found': {label!r}, 'argv': sys.argv[1:]}}))\n"
    )


def test_lint_degrades_with_install_hint_when_binary_missing(monkeypatch):
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    # Hide the module fallback too, whether or not the lint extra is installed.
    monkeypatch.setitem(sys.modules, "micar_linter", None)
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is False
    assert "eu-reg-mcp[lint]" in result["hint"]
    assert f"claude mcp add eu-reg -- {UVX_COMMAND}" in result["hint"]


def test_lint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    result = lint_whitepaper("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]


@pytest.mark.skipif(sys.platform == "win32", reason="fake micar-lint is a sh script")
@pytest.mark.parametrize(
    ("installed_in", "expected"),
    [
        pytest.param(["env"], "env", id="venv-not-activated"),
        pytest.param(["env/Scripts"], "env/Scripts", id="windows-base-install"),
        pytest.param(["env", "on-path"], "env", id="own-env-before-path"),
        pytest.param(["on-path"], "on-path", id="path-fallback"),
    ],
)
def test_lint_finds_linter_beside_interpreter_before_path(
    monkeypatch, tmp_path, installed_in, expected
):
    for place in installed_in:
        write_fake_linter(tmp_path / place, place)
    # The server runs from env/python; PATH holds only on-path/, never env/.
    monkeypatch.setattr(sys, "executable", str(tmp_path / "env" / "python"))
    monkeypatch.setenv("PATH", str(tmp_path / "on-path"))
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is True
    assert result["report"] == {"found": expected}


def test_lint_runs_linter_module_when_no_script_is_found(monkeypatch, tmp_path):
    # E.g. a user-site install whose scripts folder is not on PATH.
    site_packages, workdir = tmp_path / "site-packages", tmp_path / "workdir"
    write_fake_linter_package(site_packages, "installed")
    # The MCP client picks the working directory; a package there must not run.
    write_fake_linter_package(workdir, "workdir")
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    monkeypatch.syspath_prepend(str(site_packages))
    monkeypatch.setenv("PYTHONPATH", str(site_packages))
    monkeypatch.chdir(workdir)
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is True
    assert result["report"]["found"] == "installed"
    assert result["report"]["argv"][-1] == "--json"


def test_classify_degrades_with_install_hint_when_package_missing(monkeypatch):
    # Simulate the classify extra being absent: a None entry in sys.modules
    # makes the import fail even if the extra is installed.
    monkeypatch.setitem(sys.modules, "eu_ai_act_classifier.local_api", None)
    result = classify_ai_system("{}")
    assert result["available"] is False
    assert "eu-reg-mcp[classify]" in result["hint"]
    assert UVX_COMMAND in result["hint"]
