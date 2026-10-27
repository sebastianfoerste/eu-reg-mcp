"""Version and name agree everywhere a release reads them."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _version_tuple(text):
    return tuple(int(part) for part in text.split("."))


def test_versions_and_names_agree():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    manifest = json.loads((ROOT / "server.json").read_text("utf-8"))
    assert manifest["version"] == version
    assert {package["version"] for package in manifest["packages"]} == {version}
    first_line = (ROOT / "README.md").read_text("utf-8").splitlines()[0]
    assert first_line == f"<!-- mcp-name: {manifest['name']} -->"


def test_newest_changelog_heading_is_this_or_a_proposed_later_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    changelog = (ROOT / "CHANGELOG.md").read_text("utf-8")
    newest = re.search(r"^## (\S+) \(([^)]+)\)$", changelog, re.MULTILINE)
    assert newest, "every CHANGELOG heading is '## <version> (<date or unreleased>)'"
    heading, when = newest.groups()
    if when == "unreleased":
        assert _version_tuple(heading) >= _version_tuple(version)
    else:
        assert heading == version
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", when)
