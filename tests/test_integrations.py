import json

from eu_reg_mcp.integrations import classify_ai_system, lint_whitepaper


def test_lint_degrades_with_install_hint_when_binary_missing(monkeypatch):
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is False
    assert "eu-reg-mcp[lint]" in result["hint"]


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
    assert "eu-reg-mcp[classify]" in result["hint"]
