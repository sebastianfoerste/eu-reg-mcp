"""Optional integrations with the linter and classifier packages.

Both packages are source-available (not MIT); they install via the `lint` and
`classify` extras and degrade to an install hint when absent. Findings from
either tool are candidate flags requiring human legal review, never confirmed
deficiencies or legal conclusions — that framing is part of the contract.
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


def lint_whitepaper(whitepaper_json: str) -> dict[str, Any]:
    binary = shutil.which("micar-lint")
    if binary is None:
        return {
            "available": False,
            "hint": (
                "micar-lint is not installed. Install the optional extra: "
                "`uv pip install 'eu-reg-mcp[lint]'` (source-available license; "
                "see github.com/sebastianfoerste/micar-whitepaper-linter)."
            ),
        }
    try:
        payload = json.loads(whitepaper_json)
    except json.JSONDecodeError as error:
        return {"available": True, "error": f"whitepaper_json is not valid JSON: {error}"}

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
    }


def classify_ai_system(profile_json: str) -> dict[str, Any]:
    try:
        from eu_ai_act_classifier.local_api import classify_payload, schema_payload
    except ImportError:
        return {
            "available": False,
            "hint": (
                "eu-ai-act-classifier is not installed. Install the optional "
                "extra: `uv pip install 'eu-reg-mcp[classify]'` (source-available "
                "license; see github.com/sebastianfoerste/eu-ai-act-classifier)."
            ),
        }
    if not profile_json.strip():
        return {
            "available": True,
            "profile_schema": schema_payload(),
            "notice": "Empty profile: returning the expected SystemProfile schema.",
        }
    try:
        payload = json.loads(profile_json)
    except json.JSONDecodeError as error:
        return {"available": True, "error": f"profile_json is not valid JSON: {error}"}
    return {
        "available": True,
        "classification": classify_payload(payload),
        "notice": REVIEW_NOTICE,
    }
