# RAG-RBAC — Document Intelligence with Role-Based Access Control

A full-stack document Q&A platform built on the RAG (Retrieval-Augmented Generation) pattern. Upload documents, embed them with a local Ollama model, retrieve relevant chunks from PostgreSQL (`pgvector`), and have an LLM answer questions grounded in the retrieved context — with role-based access control enforced at the SQL layer.

## Highlights

- **Local-first AI** — embeddings and generation run on Ollama; nothing leaves your machine
- **Hybrid retrieval** — combines `pgvector` cosine similarity with PostgreSQL full-text search (`tsvector` + GIN)
- **HNSW index** on the embedding column for fast nearest-neighbor search
- **SQL-level RBAC** — the `WHERE access_level = ANY(:allowed)` filter is part of every retrieval query; no post-filtering, no leaks
- **Layered backend** — `routers → services → repositories → models`
- **Audit log** — every login, upload, view, edit, delete, and search query is recorded
- **JWT auth** with access + refresh tokens and automatic refresh in the frontend
- **Async upload pipeline** — extraction, chunking, and embedding run as FastAPI background tasks
- **Rate-limited endpoints** (configurable per route)

## Stack

| Layer        | Technology |
| ------------ | ---------- |
| Backend      | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Frontend     | React 18, TypeScript, Vite, TanStack Query, Tailwind CSS, shadcn-style components |
| Database     | PostgreSQL 16 + `pgvector` |
| LLM / Embed  | Ollama (`nomic-embed-text`, `llama3.1`) |
| Auth         | JWT (python-jose) + bcrypt |
| Container    | Docker Compose |

## Architecture

```
┌──────────────┐    JWT     ┌──────────────┐
│   React UI   │  ────────► │   FastAPI    │
│  (nginx :80) │            │  (uvicorn)   │
└──────────────┘            └──────┬───────┘
                                   │
                  ┌────────────────┼────────────────┐
                  ▼                ▼                ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
          │ Ollama       │ │ PostgreSQL   │ │ Local disk   │
          │ embeddings + │ │ + pgvector   │ │ (uploads)    │
          │ generation   │ │ + tsvector   │ │              │
          └──────────────┘ └──────────────┘ └──────────────┘
```

**RAG pipeline:**

```
query
  → Ollama embed
  → SELECT top-K chunks WHERE access_level = ANY(user_allowed_levels)
       ORDER BY embedding <=> :query_embedding
  → build prompt with numbered context
  → Ollama generate
  → return {answer, sources[]}
```

## Quick start

### Prerequisites
- Docker 24+ and Docker Compose v2
- ~8 GB free disk (mostly for Ollama models)
- (Optional) NVIDIA GPU + nvidia-container-toolkit for faster generation

### 1. Configure
```bash
cp .env.example .env
# Edit .env — at minimum, set a strong SECRET_KEY for production
```

### 2. Bring up the stack
```bash
docker compose up -d --build
```

This will:
- start Postgres (with `pgvector`), Ollama, the FastAPI backend, and the nginx-served frontend
- run Alembic migrations
- seed the demo users and sample documents if `RUN_SEED=true`

### 3. Pull the Ollama models (first run only)
```bash
./scripts/pull-models.sh
```
Pulls `nomic-embed-text` (~270 MB) and `llama3.1` (~4.7 GB). Override the models via `.env`.

### 4. Open the app
- Frontend: <http://localhost:3000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Demo credentials

| Role     | Username  | Password    | Can see |
|----------|-----------|-------------|---------|
| admin    | `admin`   | `admin123!` | all levels (public + internal + confidential + restricted) |
| manager  | `manager` | `manager123!` | up to confidential |
| user     | `user`    | `user123!`  | public + internal |
| guest    | `guest`   | `guest123!` | public only |

The seed creates one document at each access level so you can immediately observe the RBAC in action — log in as `guest` and you'll only retrieve hits from the public handbook; log in as `admin` and you'll get hits from the restricted executive comp document too.

## Roles and access levels

The role → allowed-levels matrix is in `backend/app/core/permissions.py`:

| Role    | public | internal | confidential | restricted |
|---------|:------:|:--------:|:------------:|:----------:|
| guest   | ✓      |          |              |            |
| user    | ✓      | ✓        |              |            |
| manager | ✓      | ✓        | ✓            |            |
| admin   | ✓      | ✓        | ✓            | ✓          |

This matrix is injected into every retrieval query as a SQL parameter — never post-filtered in Python.

## Project layout

```
rag-rbac-app/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile, entrypoint.sh
│   ├── requirements.txt
│   ├── alembic/                Migrations (creates schema + HNSW + GIN indexes)
│   ├── app/
│   │   ├── main.py             FastAPI app
│   │   ├── core/               config, logging, security, permissions
│   │   ├── db/                 async session
│   │   ├── models/             SQLAlchemy ORM (User, Document, Chunk, AuditLog, SearchHistory)
│   │   ├── schemas/            Pydantic v2
│   │   ├── repositories/       Data access; semantic + hybrid search SQL lives here
│   │   ├── services/           Ollama client, chunker, extractor, RAG, auth, admin
│   │   ├── api/v1/             Routers: auth, documents, search, admin
│   │   └── seed.py             Demo seed
│   └── tests/                  pytest
├── frontend/
│   ├── Dockerfile, nginx.conf
│   ├── package.json, vite.config.ts, tailwind.config.js
│   └── src/
│       ├── api/                axios client (with token refresh) + typed endpoints
│       ├── lib/                auth store (zustand), utils
│       ├── components/ui/      shadcn-style primitives
│       ├── components/layout/  AppLayout with role-aware nav
│       ├── pages/              Login, Register, Chat, Documents, History, Admin
│       └── test/               vitest
└── scripts/
    ├── pull-models.sh
    └── reset.sh
```

## API overview

The full schema is at `/docs`. Highlights below.

### Auth

| Method | Path | Notes |
| ------ | ---- | ----- |
| POST | `/api/v1/auth/register`     | Public registration. Always creates a `user`-role account. |
| POST | `/api/v1/auth/login`        | OAuth2 password flow (form-encoded). Works in Swagger UI. |
| POST | `/api/v1/auth/login/json`   | JSON-body login for the SPA. |
| POST | `/api/v1/auth/refresh`      | Exchange a refresh token for a new pair. |
| GET  | `/api/v1/auth/me`           | Current user. |

### Documents

| Method | Path | Notes |
| ------ | ---- | ----- |
| GET    | `/api/v1/documents`               | List, filtered by your role's allowed levels. |
| POST   | `/api/v1/documents`               | Multipart upload. Triggers background processing. |
| GET    | `/api/v1/documents/{id}`          | Audited view. |
| PATCH  | `/api/v1/documents/{id}`          | Owner or manager+ only. |
| DELETE | `/api/v1/documents/{id}`          | Owner or admin only. |
| POST   | `/api/v1/documents/{id}/reprocess`| Re-extract and re-embed. |

### Search (RAG)

```http
POST /api/v1/search
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "What are our working hours?",
  "top_k": 5,
  "threshold": 0.3,
  "hybrid": true,
  "generate_answer": true
}
```

Response:
```json
{
  "query": "What are our working hours?",
  "answer": "Working hours are flexible; most teams work 9am to 6pm in their local timezone [1].",
  "sources": [
    {
      "chunk_id": "…",
      "document_id": "…",
      "document_title": "Company Handbook",
      "chunk_index": 0,
      "content": "Working hours are flexible: most teams work 9am to 6pm…",
      "similarity": 0.81
    }
  ],
  "elapsed_ms": 487
}
```

### Admin (admin role required)

| Method | Path | Notes |
| ------ | ---- | ----- |
| GET    | `/api/v1/admin/users`        | Paginated user list. |
| POST   | `/api/v1/admin/users`        | Create user with any role. |
| PATCH  | `/api/v1/admin/users/{id}`   | Update role, active flag, name. |
| DELETE | `/api/v1/admin/users/{id}`   | Delete user. |
| GET    | `/api/v1/admin/audit`        | Audit log. Filter by user or action. |

## Configuration

Every option is in `.env.example` with a comment. The ones you'll most likely tune:

| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `SECRET_KEY` | JWT signing key — **must be rotated for production** | `CHANGE-ME-…` |
| `OLLAMA_EMBEDDING_MODEL` | Must match `EMBEDDING_DIMENSION` | `nomic-embed-text` (768) |
| `OLLAMA_LLM_MODEL` | Generator | `llama3.1` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Chunking | 800 / 100 chars |
| `TOP_K`, `RELEVANCE_THRESHOLD` | Retrieval defaults | 5 / 0.3 |
| `HYBRID_VECTOR_WEIGHT`, `HYBRID_TEXT_WEIGHT` | Hybrid mix | 0.7 / 0.3 |
| `MAX_UPLOAD_SIZE_MB` | Per-file limit | 50 |
| `RATE_LIMIT_*` | Per-route rate limits | various |
| `RUN_SEED` | Seed demo data on boot | `true` |

### Switching embedding models

If you want a higher-quality model like `mxbai-embed-large` (1024 dims):

1. Update `.env`:
   ```
   OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
   EMBEDDING_DIMENSION=1024
   ```
2. Edit `backend/alembic/versions/0001_initial.py` and change `EMBEDDING_DIM = 1024`. (For a live system instead, write a new migration that alters the column.)
3. Wipe the database (`./scripts/reset.sh`) and bring the stack back up.
4. `./scripts/pull-models.sh` to pull the new model.

## Development workflow

### Backend without Docker
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a local Postgres+pgvector (or the docker-compose one on localhost:5432)
export POSTGRES_HOST=localhost
export OLLAMA_BASE_URL=http://localhost:11434

alembic upgrade head
python -m app.seed        # optional
uvicorn app.main:app --reload
```

### Frontend without Docker
```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000/api/v1 npm run dev
```

### Tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### Creating a new Alembic migration
```bash
docker compose exec backend alembic revision --autogenerate -m "describe change"
docker compose exec backend alembic upgrade head
```

## Performance notes

The non-functional target — *< 2 seconds for a search over 10,000 chunks* — is dominated by two things:
- **Embedding the query** with Ollama (typically 30–80 ms on CPU for `nomic-embed-text`).
- **LLM generation** (the slow part — often 500–1500 ms even on a small model). To return results faster, send `"generate_answer": false` and use just the retrieved sources.

The retrieval SQL itself is bounded by the HNSW index (`vector_cosine_ops`, m=16, ef_construction=64) and stays in the low milliseconds at this scale. You can tune `ef_search` per session for a different speed/recall tradeoff:

```sql
SET hnsw.ef_search = 100;  -- default is 40
```

## Security checklist for production

- [ ] Replace `SECRET_KEY` with `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Set strong Postgres credentials and remove the published port from `docker-compose.yml`
- [ ] Restrict `BACKEND_CORS_ORIGINS` to your real frontend domain(s)
- [ ] Put the frontend behind HTTPS (nginx + Let's Encrypt, or a managed reverse proxy)
- [ ] Set `RUN_SEED=false` after the first boot
- [ ] Delete or change passwords for the demo users
- [ ] Tighten `RATE_LIMIT_*` based on your traffic profile
- [ ] Run regular backups of the Postgres volume and the uploads volume

## Troubleshooting

**Search returns "I retrieved relevant context but the language model is unavailable."**
Ollama is reachable but the LLM model isn't loaded. Run `./scripts/pull-models.sh`.

**Documents stuck in `processing`.**
Check `docker compose logs backend`. Usually Ollama is down or the embedding model isn't pulled. After fixing, use *Reprocess* on the document.

**`ERROR: type "vector" does not exist`** during migration.
The Postgres image must include `pgvector`. The compose file uses `pgvector/pgvector:pg16` which has it built in. If you're using a custom Postgres, install the extension first.

**429 rate-limit errors during development.**
Bump `RATE_LIMIT_*` in `.env` or comment out the `@limiter.limit(...)` decorators temporarily.

**Frontend can't reach the backend.**
The nginx config in `frontend/nginx.conf` proxies `/api/` to `http://backend:8000/api/`. If you run the frontend outside Docker, set `VITE_API_URL=http://localhost:8000/api/v1`.

## License

MIT — do what you like, no warranty.
