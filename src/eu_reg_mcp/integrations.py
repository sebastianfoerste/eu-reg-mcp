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

from pydantic import ValidationError

from eu_reg_mcp.errors import ToolFailure

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


LINT_TIMEOUT_SECONDS = 120


def linter_available() -> bool:
    return _linter_command() is not None


def classifier_available() -> bool:
    try:
        return importlib.util.find_spec("eu_ai_act_classifier.local_api") is not None
    except (ImportError, ValueError):
        return False


SCHEMA_HINT = (
    "Call with an empty profile_json to get the SystemProfile schema and an "
    "example profile."
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


def _parse_object(raw: str, argument: str, hint: str | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ToolFailure(
            "invalid_input",
            f"{argument} is not valid JSON: {error}",
            hint=hint,
            notice=REVIEW_NOTICE,
            extra={"available": True},
        ) from error
    if not isinstance(payload, dict):
        raise ToolFailure(
            "invalid_input",
            f"{argument} must be a JSON object.",
            hint=hint,
            notice=REVIEW_NOTICE,
            extra={"available": True},
        )
    return payload


def _invalid_profile(error: ValidationError) -> ToolFailure:
    """Name the failing fields; the details go in `validation_errors`."""
    details = [
        {
            # An empty location is the profile itself, e.g. a non-object "profile".
            "field": ".".join(str(part) for part in item["loc"]) or "profile_json",
            "message": item["msg"],
            "type": item["type"],
        }
        for item in error.errors(include_url=False)
    ]
    fields = ", ".join(dict.fromkeys(detail["field"] for detail in details))
    message = f"profile_json is not a valid SystemProfile. Invalid fields: {fields}."
    return ToolFailure(
        "invalid_input",
        message[:2000],
        hint=SCHEMA_HINT,
        notice=REVIEW_NOTICE,
        extra={"available": True, "validation_errors": details},
    )


def _missing_extra(package: str, extra: str) -> ToolFailure:
    return ToolFailure(
        "extra_missing",
        f"The `{extra}` extra is not installed.",
        hint=_install_hint(package, extra),
        notice=REVIEW_NOTICE,
        extra={"available": False},
    )


def lint_whitepaper(whitepaper_json: str) -> dict[str, Any]:
    command = _linter_command()
    if command is None:
        raise _missing_extra("micar-whitepaper-linter", "lint")
    payload = _parse_object(whitepaper_json, "whitepaper_json")

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
            timeout=LINT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ToolFailure(
            "timeout",
            f"micar-lint did not finish within {LINT_TIMEOUT_SECONDS} seconds.",
            hint="Retry with a shorter draft, or run micar-lint locally.",
            notice=REVIEW_NOTICE,
            extra={"available": True},
        ) from error
    finally:
        Path(path).unlink(missing_ok=True)
    if result.stdout.strip():
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ToolFailure(
                "upstream_failed",
                "micar-lint output was not JSON.",
                notice=REVIEW_NOTICE,
                extra={"available": True, "raw_output": result.stdout[:5000]},
            ) from error
        return {"available": True, "report": report, "notice": REVIEW_NOTICE}
    raise ToolFailure(
        "upstream_failed",
        (result.stderr or "linter produced no output")[:2000],
        notice=REVIEW_NOTICE,
        extra={"available": True},
    )


def classify_ai_system(profile_json: str) -> dict[str, Any]:
    try:
        from eu_ai_act_classifier.local_api import classify_payload, schema_payload
        from eu_ai_act_classifier.models import SystemProfile
    except ImportError as error:
        raise _missing_extra("eu-ai-act-classifier", "classify") from error
    if not profile_json.strip():
        required = SystemProfile.model_json_schema().get("required", [])
        return {
            "available": True,
            "profile_schema": schema_payload(),
            "example_profile": EXAMPLE_PROFILE,
            "hint": (
                "Empty profile: returning the expected SystemProfile schema and "
                "one synthetic example profile. Pass a profile as JSON to "
                f"classify it. Required fields: {', '.join(required) or 'none'}; "
                "unknown fields are rejected."
            ),
            "notice": REVIEW_NOTICE,
        }
    payload = _parse_object(profile_json, "profile_json", hint=SCHEMA_HINT)
    try:
        classification = classify_payload(payload)
    except ValidationError as error:  # the classifier rejected the profile
        raise _invalid_profile(error) from error
    return {
        "available": True,
        "classification": classification,
        "notice": REVIEW_NOTICE,
    }
