COMPOSE = docker compose --env-file .env -f infra/docker-compose.yml
API = cd apps/api && uv run

.PHONY: up down logs restart migrate revision seed reset-db dev-api dev-worker dev-web ollama-pull psql lint test

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

restart:
	$(COMPOSE) restart api worker

migrate:
	$(COMPOSE) exec api uv run alembic upgrade head

revision:
	$(COMPOSE) exec api uv run alembic revision --autogenerate -m "$(m)"

seed:
	$(COMPOSE) exec api uv run python -m api.scripts.seed

reset-db:
	set -a; . ./.env; set +a; docker run --rm postgres:16 psql "$$DATABASE_URL" \
		-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; CREATE EXTENSION IF NOT EXISTS vector;"
	$(MAKE) migrate seed

dev-api:
	$(API) uvicorn api.main:app --reload

dev-worker:
	$(API) python -m api.pipeline.worker

dev-web:
	cd apps/web && npm run dev

ollama-pull:
	ollama pull $(OLLAMA_EMBED_MODEL)
	ollama pull $(OLLAMA_CHAT_MODEL)

psql:
	set -a; . ./.env; set +a; docker run --rm -it postgres:16 psql "$$DATABASE_URL"

lint:
	$(API) ruff check .

test:
	$(API) pytest
