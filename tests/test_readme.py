"""The README is also the PyPI project description: short, with links that
work there, where relative paths do not resolve."""

import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[1]
README = (ROOT / "README.md").read_text("utf-8")
MAX_WORDS = 350

# Inline links and images, reference definitions, HTML href/src attributes.
LINK_TARGET = re.compile(
    r"\]\(\s*<?([^)\s>]+)"
    r"|^\s*\[[^\]]+\]:\s*<?([^\s>]+)"
    r"|(?:href|src)=[\"']([^\"']+)",
    re.MULTILINE,
)
REPO_FILE = re.compile(
    r"https://github\.com/sebastianfoerste/eu-reg-mcp/blob/main/([^)\s#?\"'>]+)"
    r"(?:#([\w-]+))?"
)


def _targets():
    return [next(filter(None, groups)) for groups in LINK_TARGET.findall(README)]


def _heading_anchors(markdown):
    """GitHub heading ids: lower case, punctuation dropped, spaces to hyphens."""
    headings = re.findall(r"^#+\s+(.+?)\s*$", markdown, re.MULTILINE)
    return {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}


def test_first_line_is_the_mcp_name_comment():
    first_line = README.splitlines()[0]
    assert first_line == "<!-- mcp-name: io.github.sebastianfoerste/eu-reg-mcp -->"


def test_word_count_within_limit():
    # Whitespace-separated tokens, as `wc -w README.md` counts them.
    assert len(README.split()) <= MAX_WORDS


def test_no_relative_links():
    targets = _targets()
    assert targets
    for target in targets:
        parts = urlsplit(target)
        assert parts.scheme in {"http", "https"} and parts.netloc, target


def test_repository_file_links_point_to_existing_files():
    links = REPO_FILE.findall(README)
    assert links
    for path, anchor in links:
        assert (ROOT / path).is_file(), path
        if anchor:
            text = (ROOT / path).read_text("utf-8")
            assert anchor in _heading_anchors(text), f"{path}#{anchor}"
