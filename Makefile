.PHONY: install test lint run

install:
	uv sync --extra lint --extra classify

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

run:
	uv run eu-reg-mcp
