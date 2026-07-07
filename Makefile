.PHONY: install test run

install:
	uv sync --extra dev

test:
	uv run pytest -q

run:
	uv run eu-reg-mcp
