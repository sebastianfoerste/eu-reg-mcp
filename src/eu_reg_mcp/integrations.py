"""Optional integrations with the linter and classifier packages.

Both packages are MIT-licensed and live in their own repositories. They
install via the `lint` and `classify` extras and degrade to an install hint
when absent. Findings from either tool are candidate flags requiring human
legal review, never confirmed deficiencies or legal conclusions — that
framing is part of the contract.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REVIEW_NOTICE = (
    "Deterministic rule output. Every finding is a candidate gap in the "
    "submitted text pending human legal review; extraction artifacts occur. "
    "Not legal advice."
)

UVX_WITH_EXTRAS = 'uvx --python 3.13 --from "eu-reg-mcp[lint,classify]" eu-reg-mcp'


def _install_hint(package: str, extra: str) -> str:
    return (
        f"{package} is not installed; this tool needs the `{extra}` extra. "
        f"With uvx, start the server as `{UVX_WITH_EXTRAS}` (Claude Code: "
        "`claude mcp remove eu-reg`, then "
        f"`claude mcp add eu-reg -- {UVX_WITH_EXTRAS}`). "
        "With pip, install the extra into the server's environment: "
        f'`pip install "eu-reg-mcp[{extra}]"`. '
        f"See github.com/sebastianfoerste/{package}."
    )


def _linter_command() -> list[str] | None:
    # MCP clients often start a venv's eu-reg-mcp by path without activating
    # the venv, so look in this interpreter's environment before PATH.
    if sys.executable:
        interpreter_dir = Path(sys.executable).parent
        # Console scripts sit beside python in a venv (bin/ or Scripts\) and
        # in Scripts\ below python.exe in a base Windows install.
        for script_dir in (interpreter_dir, interpreter_dir / "Scripts"):
            binary = shutil.which(str(script_dir / "micar-lint"))
            if binary is not None:
                return [binary]
    binary = shutil.which("micar-lint")
    if binary is not None:
        return [binary]
    if sys.executable and importlib.util.find_spec("micar_linter") is not None:
        # -P keeps the working directory, which the MCP client picks, off
        # sys.path, so a micar_linter/ folder there cannot shadow the package.
        return [sys.executable, "-P", "-m", "micar_linter"]
    return None


SCHEMA_HINT = (
    "Call classify_eu_ai_act_system with an empty string to get the "
    "SystemProfile JSON schema and an example profile."
)

# Synthetic example, identical to examples/credit_scoring_deployer.json in
# eu-ai-act-classifier: a bank deploying a credit scoring model (Annex III
# point 5(b)). It shows the expected shape; it describes no real system.
EXAMPLE_PROFILE: dict[str, Any] = {
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


def lint_whitepaper(whitepaper_json: str) -> dict[str, Any]:
    command = _linter_command()
    if command is None:
        return {
            "available": False,
            "hint": _install_hint("micar-whitepaper-linter", "lint"),
            "notice": REVIEW_NOTICE,
        }
    try:
        payload = json.loads(whitepaper_json)
    except json.JSONDecodeError as error:
        return {
            "available": True,
            "error": f"whitepaper_json is not valid JSON: {error}",
            "notice": REVIEW_NOTICE,
        }

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(payload, handle)
        path = handle.name
    try:
        result = subprocess.run(
            [*command, path, "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if result.stdout.strip():
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            report = {"raw_output": result.stdout[:5000]}
        return {"available": True, "report": report, "notice": REVIEW_NOTICE}
    return {
        "available": True,
        "error": (result.stderr or "linter produced no output")[:2000],
        "notice": REVIEW_NOTICE,
    }


def classify_ai_system(profile_json: str) -> dict[str, Any]:
    try:
        from eu_ai_act_classifier.local_api import classify_payload
        from eu_ai_act_classifier.models import SystemProfile
        from pydantic import ValidationError
    except ImportError:
        return {
            "available": False,
            "hint": _install_hint("eu-ai-act-classifier", "classify"),
            "notice": REVIEW_NOTICE,
        }
    if not profile_json.strip():
        profile_schema = SystemProfile.model_json_schema()
        return {
            "available": True,
            "profile_schema": profile_schema,
            "example_profile": EXAMPLE_PROFILE,
            "hint": (
                "Empty profile: returning the SystemProfile JSON schema and one "
                "synthetic example profile. Pass a profile as JSON to classify "
                "it. Required fields: "
                f"{', '.join(profile_schema.get('required', [])) or 'none'}; "
                "unknown fields are rejected."
            ),
            "notice": REVIEW_NOTICE,
        }
    try:
        payload = json.loads(profile_json)
    except json.JSONDecodeError as error:
        return {
            "available": True,
            "error": f"profile_json is not valid JSON: {error}",
            "hint": SCHEMA_HINT,
            "notice": REVIEW_NOTICE,
        }
    if not isinstance(payload, dict):
        return {
            "available": True,
            "error": "profile_json must be a JSON object (a SystemProfile).",
            "hint": SCHEMA_HINT,
            "notice": REVIEW_NOTICE,
        }
    try:
        classification = classify_payload(payload)
    except ValidationError as error:
        return {
            "available": True,
            "error": (
                "profile_json does not match the SystemProfile schema "
                f"({error.error_count()} validation error(s))."
            ),
            "validation_errors": [
                {
                    "field": ".".join(str(part) for part in detail["loc"]),
                    "message": detail["msg"],
                    "type": detail["type"],
                }
                for detail in error.errors()
            ],
            "hint": SCHEMA_HINT,
            "profile_schema": SystemProfile.model_json_schema(),
            "notice": REVIEW_NOTICE,
        }
    return {
        "available": True,
        "classification": classification,
        "notice": REVIEW_NOTICE,
    }
