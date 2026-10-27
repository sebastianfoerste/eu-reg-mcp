"""eu-reg-mcp: cited, review-gated grounding in EU regulation for AI agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("eu-reg-mcp")
except PackageNotFoundError:  # running from a source tree without metadata
    __version__ = "0+unknown"
