# NBCC Document Archival Platform — Demo/MVP Plan

## Context

NBCC (India) Limited wants to replace fragmented, hard-to-find, hard-to-share document
storage (approvals, contracts, plans, invoices, agreements — many as scans) with a
central archival system: drag-and-drop upload, auto-indexing (embeddings + a light
knowledge graph), hybrid search, a conversational "AI mode," and zone/project-scoped
access control. The immediate goal is not the production system — it's a demo/MVP
credible enough that NBCC signs the contract for the production build. That means: the
core "upload → auto-index → find it again (search or chat) → controlled sharing" loop
must work end-to-end and demo well, more than every edge case needs to be handled.

Decisions locked in with the user before this plan:
- **Fully local/self-hosted stack** — no cloud parsing/OCR/embedding APIs. Matches the
  Ollama choice already made and avoids sending (possibly sensitive, government) documents
  to third parties — also the safer story to tell NBCC.
- **3-4 week build**, aiming for a fuller demo (admin management UI included, not just the
  upload→search loop).
- **Runs locally via Docker Compose** for the demo session (no cloud deployment needed).

## Architecture Overview

```
Next.js (web) ──HTTP/JWT──> FastAPI (api) ──> Postgres (+pgvector)
                                  │                 Redis (cache + RQ job queue)
                                  │                 Neo4j (knowledge graph)
                                  │                 Ollama (embeddings + chat LLM)
                                  │
                                  └──enqueue──> RQ Worker (ingestion pipeline)
                                                    parse → OCR fallback → chunk →
                                                    embed → extract entities → graph upsert
```

All services run as containers via one `docker-compose.yml`. The API and worker share one
Python codebase/image (different entrypoints) — no need for two separately-managed
services at MVP scale.

## Tech Stack (concrete choices)

- **Web**: Next.js (App Router) + TypeScript + Tailwind.
- **API**: FastAPI + Pydantic v2, `uv` for package management, Alembic for migrations/seed.
- **Worker**: RQ (Redis Queue) — simplest fit given Redis is already in the stack for
  caching; avoids standing up Celery/RabbitMQ for an MVP.
- **Postgres** (`pgvector/pgvector` image): system of record — users, zones, projects,
  access grants, documents, chunks, embeddings (`vector` column), full-text (`tsvector`).
- **Redis**: response/query caching + RQ job broker + job status pub/sub for the UI's
  "processing status" polling.
- **Neo4j**: light knowledge graph — Document, Project, Zone, and a handful of extracted
  entity types (Organization, ContractRef, Amount, Date), connected by a small relation
  set (BELONGS_TO, REFERENCES, MENTIONS, RELATED_TO). Deliberately sparse, as scoped.
- **Ollama**: one embedding model (e.g. `nomic-embed-text`) for pgvector, one instruct
  model (e.g. `qwen2.5:7b-instruct` or `llama3.1:8b`, configurable via env) for AI-mode
  chat and for light entity/relation extraction (structured JSON prompt) feeding Neo4j.
- **Parsing/OCR** (all local, no reinvention of parsing logic):
  - `unstructured` (open-source library, not the hosted API) for layout-aware PDF
    parsing — handles born-digital PDFs and can invoke local OCR.
  - `pdf2image` + `pytesseract` (Tesseract) as the OCR fallback path for scanned
    pages/scanned-image PDFs where native text extraction yields ~no text.
- **Storage**: local filesystem volume (mounted into api+worker containers) for the demo
  — no S3/object store needed at this stage.

## Data Model (Postgres)

- `users(id, username, password_hash, role[super_admin|user], created_at)`
- `zones(id, name, code, is_default, created_at)`
- `projects(id, name, code, is_default, created_at)` — modeled as independent of zones
  (both are just optional tags on a document), matching the spec's flat "doc type,
  project, zone" inputs. **Assumption to confirm during review**, not nested.
- `user_zone_access(user_id, zone_id)`, `user_project_access(user_id, project_id)` — M2M
  grants; the default zone/project need no explicit grant (implicitly visible to everyone).
- `documents(id, filename, storage_path, doc_type, zone_id, project_id, uploaded_by,
  status[pending|parsing|embedding|graph_building|completed|failed], checksum,
  created_at, updated_at)` — `doc_type` is a small fixed enum (Approval, Contract,
  Project Plan, Invoice, Agreement, Other) rather than a manageable entity like
  zones/projects, since the spec only calls out zones/projects/users as admin-managed.
- `document_chunks(id, document_id, chunk_index, content, content_tsv, embedding vector(N))`
- `chat_sessions(id, user_id, created_at)`, `chat_messages(id, session_id, role, content,
  cited_document_ids, created_at)` — for AI-mode conversation history.

Neo4j holds `(:Document)-[:BELONGS_TO]->(:Zone|:Project)` plus extracted
`(:Document)-[:MENTIONS]->(:Entity)` edges, giving graph-based "related documents"
(shared entities/project/zone) alongside embedding-similarity based recommendations.

## Core Flows

**Ingestion**: upload → API stores file + document row (`status=pending`) → enqueues RQ
job → worker: extract text (unstructured; OCR fallback per-page via pytesseract when a
page has ~no extractable text) → chunk → embed chunks via Ollama into pgvector →
LLM-based light entity extraction → Neo4j upsert → `status=completed` (or `failed` with
reason). UI polls document status for the progress indicator.

**Delete/Reupload**: delete removes the file, its `document_chunks` rows, and
`DETACH DELETE`s its Neo4j node + orphaned entities. Reupload = same document id, wipe
derived data (chunks/embeddings/graph edges), re-run the pipeline — no version history,
matching the spec's "re-upload... related data is cleared."

**Search**: hybrid = Postgres `tsvector` rank (keyword/full-text) + pgvector cosine
similarity, combined via Reciprocal Rank Fusion. Autocomplete endpoint returns matching
documents with their direct URL, per spec. Every query is filtered by the caller's
zone/project access (super_admin bypasses; default zone/project always included).

**AI Mode**: conversational RAG — each user message triggers hybrid retrieval (scoped to
the user's access) over chunks, then a grounded Ollama chat completion (streamed to the
UI) citing source documents; conversation history stored in `chat_sessions`/`chat_messages`.

**RBAC**: JWT-based login. Super admin is a real `users` row bootstrapped at startup from
`.env` (`SUPERADMIN_USERNAME`/`SUPERADMIN_PASSWORD`), so it flows through the same auth
path as everyone else. All other users have `role=user`; their effective zone/project
access = explicit grants ∪ {default zone, default project}. A single reusable
access-filter helper (used by documents/search/chat endpoints) is the sole place this
logic lives.

## Monorepo Layout

```
nbcc-archive/
  apps/
    web/            Next.js + TS + Tailwind
    api/            FastAPI app, Alembic migrations, RQ worker entrypoint, seed script
  infra/
    docker-compose.yml
    postgres/init/  (enable pgvector extension)
  scripts/          bash helpers (wait-for-services, ollama model pull)
  Makefile
  .env.example
```

`apps/api` contains both the FastAPI app and the worker module (`api/worker.py`, run via
`rq worker` as a separate container command from the same image) — one Python
dependency set, two entrypoints, no duplicated code for models/DB access.

## Docker Compose Services

`postgres` (pgvector image), `redis`, `neo4j`, `ollama` (+ a one-shot init step that pulls
the embedding/chat models), `api`, `worker`, `web`.

## Makefile Targets

`up`, `down`, `logs`, `migrate`, `seed`, `reset-db`, `dev-web`, `dev-api`, `dev-worker`,
`ollama-pull`, `psql`, `lint`, `test`.

## API Surface (FastAPI routers)

- `auth`: `POST /login`, `POST /logout`, `GET /me`
- `users`: CRUD + zone/project assignment (super_admin only)
- `zones`, `projects`: CRUD (super_admin), list (scoped for regular users)
- `documents`: upload, list/browse (filtered), get, delete, reupload, status, related,
  download (access-checked)
- `search`: `GET /search` (hybrid), `GET /search/autocomplete` (doc URL results)
- `chat`: create session, post message (streamed), get session history

## Frontend Pages (Next.js)

`/login`, `/upload` (drag-drop + zone/project/doc-type inputs + live status), `/documents`
(search bar with Search/AI Mode toggle, filters, results + related-docs panel), `/chat`
(or folded into `/documents` as the AI Mode view), `/admin/zones`, `/admin/projects`,
`/admin/users` (super_admin-guarded), shared authenticated layout with logout.

## Delivery Phases (3-4 weeks)

1. **Week 1 — Foundation**: monorepo + docker-compose (postgres/pgvector, redis, neo4j,
   ollama), Alembic models/migrations, seed script (default zone/project, super admin),
   JWT auth, zones/projects/users CRUD + minimal admin UI, Next.js scaffold with auth guard.
2. **Week 2 — Ingestion**: upload UI + API, RQ pipeline (parse, OCR fallback, chunk,
   embed into pgvector), live status UI, delete/reupload with cascade cleanup.
3. **Week 3 — Search & Graph**: hybrid search (tsvector + pgvector + RRF), autocomplete
   with doc URLs, LLM-based entity extraction into Neo4j, related-documents panel
   (graph + embedding similarity), search UI polish.
4. **Week 4 — AI Mode & Hardening**: conversational RAG chat (streamed, cited sources),
   end-to-end access-control verification, demo sample data/story, README/demo runbook,
   bug bash.

## Verification Plan

- `make up && make migrate && make seed` brings up the full stack with a super admin,
  default zone/project, and a couple of sample zones/projects/users/documents.
- Manual E2E script: login as super admin → create a zone/project → create a
  zone-scoped user → login as that user → upload one native-text PDF and one scanned
  PDF → watch status reach `completed` for both (confirms OCR path) → run a keyword and
  a semantic search query → verify hybrid ranking → use AI Mode to ask a question
  answerable only from an uploaded doc, confirm a grounded/cited answer → confirm the
  scoped user cannot see another zone's non-default documents → delete a document and
  confirm its chunks are gone from Postgres and its node is gone from Neo4j (via Neo4j
  browser query).
- A small pytest suite for the access-filter helper and ingestion status transitions,
  since this is the logic a customer demo most needs to not embarrassingly break.

## Open Assumptions to Confirm at Kickoff

- `doc_type` is a fixed enum, not a super-admin-managed entity (only zones/projects/users
  are called out as manageable in the spec).
- Projects and zones are independent/orthogonal tags on a document, not nested.
- No document version history is kept — reupload replaces in place.
- Local filesystem storage is fine for the demo (production would likely move to
  object storage, out of scope here).
- Local Ollama models need reasonable hardware (recommend 16GB+ RAM on the machine
  running the demo) for acceptable latency during a live session.
