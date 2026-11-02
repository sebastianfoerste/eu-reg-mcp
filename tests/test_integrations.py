import importlib.util
import json
import subprocess
import sys

import pytest

from eu_reg_mcp.errors import ToolFailure
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
    with pytest.raises(ToolFailure) as failure:
        lint_whitepaper(json.dumps({"title": "x"}))
    result = failure.value.payload()
    assert result["code"] == "extra_missing"
    assert result["available"] is False
    assert "eu-reg-mcp[lint]" in result["hint"]
    assert f"claude mcp add eu-reg -- {UVX_COMMAND}" in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


def test_lint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    with pytest.raises(ToolFailure) as failure:
        lint_whitepaper("{not json")
    result = failure.value.payload()
    assert result["code"] == "invalid_input"
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
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system("{}")
    result = failure.value.payload()
    assert result["code"] == "extra_missing"
    assert result["available"] is False
    assert "eu-reg-mcp[classify]" in result["hint"]
    assert UVX_COMMAND in result["hint"]
    assert result["notice"] == REVIEW_NOTICE


def test_lint_timeout_is_a_timeout_error(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )

    def slow(*_args, **kwargs):
        raise subprocess.TimeoutExpired("micar-lint", kwargs["timeout"])

    monkeypatch.setattr("eu_reg_mcp.integrations.subprocess.run", slow)
    with pytest.raises(ToolFailure) as failure:
        lint_whitepaper(json.dumps({"type": "other", "sections": {}}))
    assert failure.value.code == "timeout"


def test_lint_non_json_output_is_upstream_failure(monkeypatch):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.subprocess.run",
        lambda *_a, **_k: subprocess.CompletedProcess([], 0, "not json", ""),
    )
    with pytest.raises(ToolFailure) as failure:
        lint_whitepaper(json.dumps({"type": "other", "sections": {}}))
    assert failure.value.code == "upstream_failed"
    assert failure.value.payload()["raw_output"] == "not json"


@pytest.mark.parametrize("raw", ["[]", '"text"'])
def test_inputs_must_be_json_objects(monkeypatch, raw):
    monkeypatch.setattr(
        "eu_reg_mcp.integrations.shutil.which", lambda _: "/usr/bin/micar-lint"
    )
    with pytest.raises(ToolFailure) as failure:
        lint_whitepaper(raw)
    assert failure.value.code == "invalid_input"


def test_classify_invalid_profile_is_invalid_input():
    pytest.importorskip("eu_ai_act_classifier.local_api")
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system("{}")
    assert failure.value.code == "invalid_input"
    assert "SystemProfile" in failure.value.message


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
def test_classify_rejects_invalid_profile_as_invalid_input():
    # Classifier 0.2.2 rejects a non-ISO date with a pydantic ValidationError.
    profile = {
        "name": "x",
        "roles": ["provider"],
        "annex_iii_area": "III.4.a",
        "placing_on_market_date": "March 2026",
    }
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system(json.dumps(profile))
    body = failure.value.payload()
    assert body["code"] == "invalid_input" and body["available"] is True
    assert "not a valid SystemProfile" in body["error"]
    assert "placing_on_market_date" in body["error"]


@requires_classifier
def test_classify_passes_other_value_errors_through(monkeypatch):
    # Only a pydantic ValidationError means the profile is invalid. Any other
    # ValueError is the classifier's own failure; the server reports it as
    # upstream_failed (see test_mcp_contract.py).
    def boom(_payload):
        raise ValueError("classifier bug")

    monkeypatch.setattr("eu_ai_act_classifier.local_api.classify_payload", boom)
    with pytest.raises(ValueError, match="classifier bug"):
        classify_ai_system(json.dumps({"name": "x", "roles": ["provider"]}))


@requires_classifier
@pytest.mark.parametrize("profile_json", ["[]", "123", '"x"', "null"])
def test_classify_rejects_non_object_json_as_invalid_input(profile_json):
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system(profile_json)
    assert failure.value.code == "invalid_input"
    assert failure.value.message == "profile_json must be a JSON object."
    assert failure.value.hint == SCHEMA_HINT


# --- classify: empty profile, rejected profiles, a high-risk deployer --------


@requires_classifier
@pytest.mark.parametrize("empty", ["", "   ", "\n"])
def test_classify_empty_profile_returns_schema_and_example(empty):
    result = classify_ai_system(empty)
    assert result["available"] is True
    assert result["notice"] == REVIEW_NOTICE
    schema = result["profile_schema"]
    # The classifier's own schema payload, unchanged: allowed values plus the
    # artifacts, dossier schema and review posture.
    assert {"roles", "annex_iii_areas", "prohibited_practices"} <= set(schema)
    assert {"artifacts", "dossier_schema", "review_posture"} <= set(schema)
    assert "III.5.b" in schema["annex_iii_areas"]
    # The field-level JSON schema names every field, including the singular
    # annex_iii_area that the plural annex_iii_areas list above does not.
    json_schema = result["profile_json_schema"]
    assert json_schema["required"] == ["name"]
    assert json_schema["additionalProperties"] is False
    assert {"annex_iii_area", "derogation", "placing_on_market_date"} <= set(
        json_schema["properties"]
    )
    assert result["example_profile"] == EXAMPLE_PROFILE
    assert "Required fields: name;" in result["hint"]
    assert "classification" not in result


@requires_classifier
def test_example_profile_is_valid_and_classifies():
    result = classify_ai_system(json.dumps(EXAMPLE_PROFILE))
    assert result["available"] is True
    assert result["classification"]["risk_tier"] == "high_risk"


@requires_classifier
def test_classify_invalid_json_carries_hint_and_notice():
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system("{not json")
    body = failure.value.payload()
    assert body["code"] == "invalid_input" and body["available"] is True
    assert "not valid JSON" in body["error"]
    assert body["hint"] == SCHEMA_HINT
    assert body["notice"] == REVIEW_NOTICE


@requires_classifier
def test_classify_unknown_field_returns_validation_errors():
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system(json.dumps({"name": "x", "use_case": "credit"}))
    body = failure.value.payload()
    assert body["code"] == "invalid_input" and body["available"] is True
    assert body["error"] == (
        "profile_json is not a valid SystemProfile. Invalid fields: use_case."
    )
    assert body["validation_errors"] == [
        {
            "field": "use_case",
            "message": "Extra inputs are not permitted",
            "type": "extra_forbidden",
        }
    ]
    assert body["hint"] == SCHEMA_HINT
    assert body["notice"] == REVIEW_NOTICE
    assert "profile_schema" not in body


@requires_classifier
def test_classify_missing_name_and_bad_enum_are_reported():
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system(json.dumps({"annex_iii_area": "III.99"}))
    body = failure.value.payload()
    fields = [error["field"] for error in body["validation_errors"]]
    assert sorted(fields) == ["annex_iii_area", "name"]
    for field in fields:
        assert field in body["error"]
    assert "errors.pydantic.dev" not in json.dumps(body)


@requires_classifier
def test_classify_error_on_the_profile_itself_names_profile_json():
    # classify_payload validates payload["profile"] when present.
    with pytest.raises(ToolFailure) as failure:
        classify_ai_system(json.dumps({"profile": 5}))
    body = failure.value.payload()
    assert body["validation_errors"][0]["field"] == "profile_json"
    assert body["error"].endswith("Invalid fields: profile_json.")


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
