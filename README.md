# NBCC Document Archive — Demo/MVP

A central document archival system for NBCC (India) Limited: drag-and-drop upload,
automatic indexing (embeddings + a light knowledge graph), hybrid search, a
conversational "AI mode," and zone/project-scoped access control.

See `/Users/narendra/.claude/plans/steady-floating-clarke.md` (or ask for a copy) for the
full architecture writeup. This README only covers running the demo.

## Stack

- **Web**: Next.js + TypeScript + Tailwind (`apps/web`)
- **API**: FastAPI + SQLAlchemy + Alembic, managed with `uv` (`apps/api`)
- **Worker**: RQ background worker for document ingestion (same codebase as the API)
- **Postgres** (+pgvector): system of record, full-text + vector search
- **Redis**: caching and the RQ job queue
- **Neo4j**: a deliberately sparse knowledge graph (documents, zones, projects, a
  handful of extracted entities) used for "related documents"
- **Ollama**: local embeddings + chat model — nothing is sent to a third-party API

`docker-compose.yml` only runs the API, the worker, and the web app — **Postgres,
Redis, Neo4j, and Ollama are not containers here**:

- Postgres/Redis/Neo4j point at whatever's in `DATABASE_URL` / `REDIS_URL` /
  `NEO4J_URI` in `.env`. For this project that's a dedicated `nbcc_archive` Postgres
  database (with `pgvector` enabled), a dedicated Redis db index, and a Neo4j instance
  used exclusively by this project — reusing already-running infrastructure instead of
  three more containers. Point them at local instances instead if you'd rather keep
  this fully self-contained; nothing in the code cares which, **except**: Neo4j
  Community Edition can't isolate multiple databases the way Postgres can, so whatever
  Neo4j instance you use must be dedicated to this project alone — never a shared one
  with other data in it (the app's document-delete cleanup runs an unscoped
  `MATCH (e:Entity)...DELETE` that would happily delete someone else's nodes too).
- Ollama runs natively on your host — the `api`/`worker` containers reach it via
  `host.docker.internal` instead of a second Ollama-in-Docker, avoiding a duplicate
  multi-GB model download.

Note the tradeoff if you point at a shared/remote Postgres, Redis, or Neo4j: document
content, embeddings, and the knowledge graph then leave your machine, which cuts
against the "nothing leaves the machine" pitch this stack was otherwise built around
for NBCC. Fine for local dev speed; worth switching back to local instances for
anything customer-facing.

## First-time setup

```bash
ollama pull nomic-embed-text   # or `make ollama-pull` after setting .env
ollama pull llama3.1           # any chat model you already have works — see .env

cp .env.example .env         # set DATABASE_URL, REDIS_URL, NEO4J_URI, SUPERADMIN_PASSWORD, SECRET_KEY, etc.
make up                      # builds and starts api, worker, web
make migrate                 # applies the Alembic schema
make seed                    # bootstraps the super admin, default zone/project, sample data
```

Once up:

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs

Log in with the super admin credentials from `.env` (`SUPERADMIN_USERNAME` /
`SUPERADMIN_PASSWORD`), or the seeded demo user `zone.northern` / `demo1234` (scoped to
the Northern Zone and the Delhi Metro Extension project) to see access control in action.

## Everyday commands

| Command | What it does |
| --- | --- |
| `make up` | Build and start api, worker, web |
| `make down` | Stop all containers |
| `make logs` | Tail logs from all services |
| `make migrate` | Apply Alembic migrations |
| `make revision m="message"` | Generate a new migration from model changes |
| `make seed` | Re-run the idempotent seed script |
| `make reset-db` | Drop and recreate the `public` schema on `DATABASE_URL`, then migrate + seed |
| `make dev-api` / `make dev-worker` / `make dev-web` | Run one service outside Docker, against the same Postgres/Redis/Neo4j |
| `make psql` | Open a psql shell against `DATABASE_URL` (via a throwaway `postgres:16` container) |
| `make test` | Run the API test suite |

## Notes for whoever picks this up next

- `unstructured`'s "auto" parsing strategy handles both born-digital and scanned PDFs —
  it decides per page whether to fall back to local Tesseract OCR, so there's no
  bespoke OCR-detection code to maintain.
- The knowledge graph is intentionally shallow (a handful of entity types, extracted
  from a bounded excerpt per document) — it exists to power "related documents" and
  light structure, not to be an exhaustive knowledge base.
- AI Mode chat is currently a synchronous request/response (not token-streamed) for
  simplicity — the RAG retrieval and grounding both work, streaming would be a
  follow-up if the demo needs the token-by-token typing effect.
- `doc_type` is a fixed enum (approval/contract/project_plan/invoice/agreement/other)
  rather than a super-admin-managed entity like zones/projects — flagged as an
  assumption during planning, easy to promote to a managed table later if needed.
