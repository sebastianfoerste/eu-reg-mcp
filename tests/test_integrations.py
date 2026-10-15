import json
import shutil
import sys
from pathlib import Path

import pytest

from eu_reg_mcp.integrations import (
    EXAMPLE_PROFILE,
    PIP_WITH_EXTRAS,
    REVIEW_NOTICE,
    UVX_WITH_EXTRAS,
    classify_ai_system,
    lint_whitepaper,
)

# Synthetic Annex III point 5(b) deployer, as in eu-ai-act-classifier's
# examples/credit_scoring_deployer.json.
BANK_CREDIT_DEPLOYER = {
    "name": "BankCo loan underwriting",
    "description": (
        "A bank deploying a third-party credit scoring model for consumer "
        "loan decisions."
    ),
    "roles": ["deployer"],
    "purpose": "Loan underwriting",
    "sector": "Banking",
    "annex_iii_area": "III.5.b",
}


@pytest.fixture
def classifier():
    """Skip unless the `classify` extra is installed."""
    return pytest.importorskip("eu_ai_act_classifier.local_api")


@pytest.fixture
def classifier_missing(monkeypatch):
    """Make `import eu_ai_act_classifier...` fail, installed or not."""
    for name in list(sys.modules):
        if name == "eu_ai_act_classifier" or name.startswith("eu_ai_act_classifier."):
            monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setitem(sys.modules, "eu_ai_act_classifier", None)


# --- lint -----------------------------------------------------------------


def test_lint_degrades_with_install_hint_when_binary_missing(monkeypatch):
    monkeypatch.setattr("eu_reg_mcp.integrations.shutil.which", lambda _: None)
    result = lint_whitepaper(json.dumps({"title": "x"}))
    assert result["available"] is False
    assert f"`{UVX_WITH_EXTRAS}`" in result["hint"]
    assert f"`{PIP_WITH_EXTRAS}`" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


def test_lint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    result = lint_whitepaper("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]
    assert result["notice"] == REVIEW_NOTICE


@pytest.mark.skipif(shutil.which("micar-lint") is None, reason="needs the `lint` extra")
def test_lint_runs_installed_linter_on_synthetic_draft():
    draft = {
        "title": "Synthetic test draft",
        "type": "other",
        "sections": {"summary": "A token.", "risk_warning": ""},
    }
    result = lint_whitepaper(json.dumps(draft))
    assert result["available"] is True
    assert result["notice"] == REVIEW_NOTICE
    report = result["report"]
    assert report["whitepaper_type"] == "other"
    assert report["findings"], "a near-empty draft must produce candidate findings"
    assert all(finding["citation"] for finding in report["findings"])


# --- classify: missing extra ------------------------------------------------


def test_classify_degrades_with_install_hint_when_package_missing(classifier_missing):
    result = classify_ai_system("{}")
    assert result["available"] is False
    assert f"`{UVX_WITH_EXTRAS}`" in result["hint"]
    assert f"`{PIP_WITH_EXTRAS}`" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


# --- classify: with the extra -------------------------------------------------


@pytest.mark.parametrize("empty", ["", "   ", "\n"])
def test_classify_empty_profile_returns_json_schema_and_example(classifier, empty):
    result = classify_ai_system(empty)
    assert result["available"] is True
    assert result["notice"] == REVIEW_NOTICE
    schema = result["profile_schema"]
    assert schema["title"] == "SystemProfile"
    assert schema["required"] == ["name"]
    assert {"name", "roles", "annex_iii_area", "derogation"} <= set(
        schema["properties"]
    )
    assert schema["additionalProperties"] is False
    assert result["example_profile"] == EXAMPLE_PROFILE
    assert "Required fields: name" in result["hint"]


def test_example_profile_is_valid_and_classifies(classifier):
    result = classify_ai_system(json.dumps(EXAMPLE_PROFILE))
    assert result["available"] is True
    assert result["classification"]["risk_tier"] == "high_risk"


def test_classify_invalid_json_carries_hint_and_notice(classifier):
    result = classify_ai_system("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]
    assert "empty string" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


def test_classify_rejects_non_object_json(classifier):
    result = classify_ai_system("[1, 2]")
    assert result["available"] is True
    assert "JSON object" in result["error"]
    assert result["notice"] == REVIEW_NOTICE


def test_classify_unknown_field_returns_validation_error_with_schema(classifier):
    result = classify_ai_system(json.dumps({"name": "x", "use_case": "credit"}))
    assert result["available"] is True
    assert "SystemProfile schema" in result["error"]
    assert {"field": "use_case", "type": "extra_forbidden"} == {
        key: result["validation_errors"][0][key] for key in ("field", "type")
    }
    assert result["profile_schema"]["title"] == "SystemProfile"
    assert "empty string" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


def test_classify_missing_name_and_bad_enum_are_reported(classifier):
    result = classify_ai_system(json.dumps({"annex_iii_area": "III.99"}))
    fields = {error["field"] for error in result["validation_errors"]}
    assert fields == {"name", "annex_iii_area"}
    assert "classification" not in result


def test_classify_annex_iii_5b_deployer_is_high_risk_with_art_26_and_27(classifier):
    result = classify_ai_system(json.dumps(BANK_CREDIT_DEPLOYER))
    assert result["available"] is True
    assert result["notice"] == REVIEW_NOTICE
    classification = result["classification"]
    assert classification["system"] == "BankCo loan underwriting"
    assert classification["risk_tier"] == "high_risk"
    assert classification["roles"] == ["deployer"]
    articles = {obligation["article"] for obligation in classification["obligations"]}
    assert {"Art. 26 AIA", "Art. 27 AIA"} <= articles
    deployer_items = {
        item["article"]
        for item in classification["obligation_graph"]
        if item["actor"] == "deployer"
    }
    assert {"Art. 26 AIA", "Art. 27 AIA"} <= deployer_items
    assert classification["disclaimer"]


def test_install_hint_names_the_pypi_uvx_and_pip_forms_with_both_extras():
    assert UVX_WITH_EXTRAS == "uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp"
    assert PIP_WITH_EXTRAS == "pip install 'eu-reg-mcp[lint,classify]'"
    # docs/tools.md describes the hint by quoting both commands.
    tools_doc = (Path(__file__).parents[1] / "docs" / "tools.md").read_text(
        encoding="utf-8"
    )
    for command in (UVX_WITH_EXTRAS, PIP_WITH_EXTRAS):
        assert "git+" not in command
        assert f"`{command}`" in tools_doc
