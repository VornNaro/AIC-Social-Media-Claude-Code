# Social Hub

A social media web application — user profiles, JWT authentication, posts, comments, reactions, and shares — with a modern feed UI.

| Layer | Stack |
|---|---|
| Frontend | Next.js (App Router, TypeScript) · Tailwind CSS · shadcn/ui · TanStack React Query |
| Backend | FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 |
| Database | PostgreSQL 17 |
| Auth | JWT access + refresh rotation · httpOnly cookies |
| Runtime | Docker Compose (postgres · backend · frontend) |

## Quickstart

```bash
# 1. env files
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# 2. run everything
docker compose up --build
```

- App: http://localhost:3000
- API docs (OpenAPI): http://localhost:8000/docs
- Health: http://localhost:8000/health

### Recommended dev loop (fastest HMR)

```bash
docker compose up postgres backend     # DB + API in Docker, hot reload
cd frontend && npm install && npm run dev
```

> ⚠️ Never install backend Python deps on the host — the backend is Docker-only (`python:3.12-slim`). See `docs/01-environment-setup.md`.

### Tests

```bash
docker compose run --rm backend pytest
```

## Documentation

Complete implementation specification in [`docs/`](docs/):

| Doc | Topic |
|---|---|
| [00-project-overview](docs/00-project-overview.md) | scope, stack, decisions |
| [01-environment-setup](docs/01-environment-setup.md) | tools, env files |
| [02-architecture](docs/02-architecture.md) | system + repo + Docker design |
| [03-database](docs/03-database.md) | ERD, models, constraints |
| [04-api](docs/04-api.md) | endpoint contracts |
| [05-auth-flow](docs/05-auth-flow.md) | JWT lifecycle, cookies |
| [06-frontend](docs/06-frontend.md) | pages, components, data layer |
| [07-testing](docs/07-testing.md) | pytest strategy + test matrix |
| [08-implementation-phases](docs/08-implementation-phases.md) | build order + verification |

Agentic-coding guides: [`CLAUDE.md`](CLAUDE.md) (root), [`backend/CLAUDE.md`](backend/CLAUDE.md), [`frontend/CLAUDE.md`](frontend/CLAUDE.md).

## Project status

- [x] Phase 0 — documentation + repo scaffold
- [ ] Phase 1 — backend foundation (`/health`, Docker)
- [ ] Phase 2 — models + migrations
- [ ] Phase 3 — authentication
- [ ] Phase 4 — posts / comments / reactions / shares API
- [ ] Phase 5 — frontend scaffold
- [ ] Phase 6 — auth UI + route protection
- [ ] Phase 7 — feed & feature UI
- [ ] Phase 8 — full dockerization
- [ ] Phase 9 — seed data + final test pass
