import importlib.util
import json
import sys

import pytest

from eu_reg_mcp.integrations import (
    EXAMPLE_PROFILE,
    REVIEW_NOTICE,
    SCHEMA_HINT,
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


UVX_COMMAND = 'uvx --python 3.13 --from "eu-reg-mcp[lint,classify]" eu-reg-mcp'

# For tests that run the installed classifier. CI installs the classify extra,
# so they run there; a missing package, not a broken one, skips them.
requires_classifier = pytest.mark.skipif(
    importlib.util.find_spec("eu_ai_act_classifier") is None,
    reason="eu-ai-act-classifier (the classify extra) is not installed",
)


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
    assert result["notice"] == REVIEW_NOTICE


def test_lint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    result = lint_whitepaper("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]
    assert result["notice"] == REVIEW_NOTICE


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


@pytest.mark.skipif(
    importlib.util.find_spec("micar_linter") is None, reason="needs the `lint` extra"
)
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


def test_classify_degrades_with_install_hint_when_package_missing(monkeypatch):
    # Simulate the classify extra being absent: a None entry in sys.modules
    # makes the import fail even if the extra is installed.
    monkeypatch.setitem(sys.modules, "eu_ai_act_classifier.local_api", None)
    result = classify_ai_system("{}")
    assert result["available"] is False
    assert "eu-reg-mcp[classify]" in result["hint"]
    assert UVX_COMMAND in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


# --- classify: with the extra -------------------------------------------------


@requires_classifier
@pytest.mark.parametrize("empty", ["", "   ", "\n"])
def test_classify_empty_profile_returns_json_schema_and_example(empty):
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


@requires_classifier
def test_example_profile_is_valid_and_classifies():
    result = classify_ai_system(json.dumps(EXAMPLE_PROFILE))
    assert result["available"] is True
    assert result["classification"]["risk_tier"] == "high_risk"


@requires_classifier
def test_classify_invalid_json_carries_hint_and_notice():
    result = classify_ai_system("{not json")
    assert result["available"] is True
    assert "not valid JSON" in result["error"]
    assert "empty string" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


@requires_classifier
def test_classify_unknown_field_returns_validation_error_with_schema():
    result = classify_ai_system(json.dumps({"name": "x", "use_case": "credit"}))
    assert result["available"] is True
    assert "not a valid SystemProfile" in result["error"]
    assert {"field": "use_case", "type": "extra_forbidden"} == {
        key: result["validation_errors"][0][key] for key in ("field", "type")
    }
    assert result["profile_schema"]["title"] == "SystemProfile"
    assert "empty string" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


@requires_classifier
def test_classify_missing_name_and_bad_enum_are_reported():
    result = classify_ai_system(json.dumps({"annex_iii_area": "III.99"}))
    fields = {error["field"] for error in result["validation_errors"]}
    assert fields == {"name", "annex_iii_area"}
    assert "classification" not in result


@requires_classifier
def test_classify_annex_iii_5b_deployer_is_high_risk_with_art_26_and_27():
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


@requires_classifier
def test_classify_timeline_has_2_december_2026_entry():
    # Regulation (EU) 2026/1744 entries, new in classifier 0.2.2 (the floor of
    # the classify extra); 0.2.0 and 0.2.1 have none.
    profile = {"name": "x", "roles": ["provider"], "annex_iii_area": "III.4.a"}
    result = classify_ai_system(json.dumps(profile))
    assert result["available"] is True
    dates = [entry["applies_from"] for entry in result["classification"]["timeline"]]
    assert "2026-12-02" in dates


@requires_classifier
def test_classify_returns_error_for_invalid_profile():
    # Classifier 0.2.2 rejects a non-ISO date with a pydantic ValidationError.
    profile = {
        "name": "x",
        "roles": ["provider"],
        "annex_iii_area": "III.4.a",
        "placing_on_market_date": "March 2026",
    }
    result = classify_ai_system(json.dumps(profile))
    assert result["available"] is True
    assert "classification" not in result
    assert "not a valid SystemProfile" in result["error"]
    assert "placing_on_market_date" in result["error"]


@requires_classifier
@pytest.mark.parametrize("profile_json", ["[]", "123", '"x"', "null"])
def test_classify_returns_error_for_non_object_json(profile_json):
    result = classify_ai_system(profile_json)
    assert result == {
        "available": True,
        "error": "profile_json must be a JSON object",
        "hint": SCHEMA_HINT,
        "notice": REVIEW_NOTICE,
    }
