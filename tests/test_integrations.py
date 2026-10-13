import json

from eu_reg_mcp.integrations import (
    INSTALL_WITH_EXTRAS,
    classify_ai_system,
    lint_whitepaper,
)

SOURCE = "eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp"


def test_lint_degrades_with_install_hint_when_binary_missing(monkeypatch):
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is False
    assert INSTALL_WITH_EXTRAS in result["hint"]


def test_lint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    result = lint_whitepaper("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]


def test_classify_degrades_with_install_hint_when_package_missing():
    # eu_ai_act_classifier is not installed in the test environment.
    result = classify_ai_system("{}")
    assert result["available"] is False
    assert INSTALL_WITH_EXTRAS in result["hint"]


def test_install_hint_names_the_git_source_with_both_extras():
    # A bare `eu-reg-mcp[lint]` would resolve against PyPI, not this repository.
    assert f"--from '{SOURCE}' eu-reg-mcp" in INSTALL_WITH_EXTRAS
