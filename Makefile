.PHONY: setup dev test build check bank admin ai-models
setup:
	uv sync --project backend --frozen
	npm --prefix frontend ci
	cd backend && .venv/bin/python -m app.cli migrate
	cd backend && .venv/bin/python -m app.cli bank
bank:
	cd backend && .venv/bin/python -m app.cli bank
	cd backend && .venv/bin/python -m app.cli verify-bank
dev:
	python3 scripts/dev.py
test:
	cd backend && .venv/bin/pytest -q
	npm --prefix frontend test
build:
	npm --prefix frontend run build
check: test build
admin:
	cd backend && .venv/bin/python -m app.cli admin
ai-models:
	backend/.venv/bin/python scripts/list_ai_models.py
