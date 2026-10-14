.PHONY: install install-all test smoke run

install:
	uv sync --extra dev

install-all:
	uv sync --extra dev --extra classify --extra lint

test:
	uv run pytest -q

smoke:
	uv run --no-project --with 'mcp>=1.2,<2' python scripts/smoke_list_tools.py -- \
		uvx --refresh --from '.[classify,lint]' eu-reg-mcp

run:
	uv run eu-reg-mcp
