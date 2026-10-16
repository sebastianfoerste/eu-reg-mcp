.PHONY: install test lint smoke run

install:
	uv sync --extra dev --extra lint --extra classify

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

smoke:
	uv run --isolated --no-project --with 'mcp>=1.2,<2' python scripts/smoke_list_tools.py -- \
		uvx --python 3.13 --refresh --from '.[lint,classify]' eu-reg-mcp

run:
	uv run eu-reg-mcp
