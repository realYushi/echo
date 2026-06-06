.PHONY: dev up down backend-dev frontend-dev install lint test db-migrate db-revision

dev:
	./scripts/dev.sh

up:
	docker-compose up -d

down:
	docker-compose down

backend-dev:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

lint:
	cd backend && ruff check . && ruff format --check . && mypy .
	cd frontend && npm run lint

test:
	cd backend && pytest
	cd frontend && npm run test

db-migrate:
	cd backend && alembic upgrade head

db-revision:
	cd backend && alembic revision --autogenerate -m "$(MSG)"
