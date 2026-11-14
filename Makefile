PY ?= .venv/bin/python

.PHONY: venv test lint

venv:
	uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check .
