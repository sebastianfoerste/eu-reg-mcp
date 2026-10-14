"""Optional integrations with the linter and classifier packages.

Both packages are MIT-licensed and live in their own repositories. They
install via the `lint` and `classify` extras and degrade to an install hint
when absent. Findings from either tool are candidate flags requiring human
legal review, never confirmed deficiencies or legal conclusions — that
framing is part of the contract.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REVIEW_NOTICE = (
    "Deterministic rule output. Every finding is a candidate gap in the "
    "submitted text pending human legal review; extraction artifacts occur. "
    "Not legal advice."
)

# The package and both extras install from GitHub, not from PyPI.
INSTALL_WITH_EXTRAS = (
    "uvx --from 'eu-reg-mcp[lint,classify] @ "
    "git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp"
)


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
    binary = shutil.which("micar-lint")
    if binary is None:
        return {
            "available": False,
            "hint": (
                "micar-lint is not installed. Start the server with the "
                f"optional extras: `{INSTALL_WITH_EXTRAS}` "
                "(see github.com/sebastianfoerste/micar-whitepaper-linter)."
            ),
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
            [binary, path, "--json"],
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
            "hint": (
                "eu-ai-act-classifier is not installed. Start the server with "
                f"the optional extras: `{INSTALL_WITH_EXTRAS}` "
                "(see github.com/sebastianfoerste/eu-ai-act-classifier)."
            ),
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
