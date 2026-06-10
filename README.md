# SchoolMate

![CI](https://github.com/VornNaro/AIC-Social-Media-Claude-Code/actions/workflows/ci.yml/badge.svg)

> Reconnecting classmates. Reliving memories. Building together.

**SchoolMate** is a warm, nostalgic social network for reconnecting with school classmates — a *yearbook that never closes*. Find your old crowd, share memories, and organize reunions.

It started as a generic social app (JWT auth, posts, comments, reactions, shares) and was extended into the SchoolMate alumni network from a Claude Design handoff: **schools/communities, classmate connections, and reunions with RSVPs**, wrapped in a warm blue/coral/cream design.

| Layer | Stack |
|---|---|
| Frontend | Next.js 16 (App Router, TS) · Tailwind CSS v4 · Base UI / shadcn · TanStack React Query |
| Backend | FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 |
| Database | PostgreSQL 17 |
| Auth | JWT access + refresh rotation · httpOnly cookies (set by Next.js route handlers) |
| Runtime | Docker Compose (postgres · backend · frontend) |
| CI/CD | GitHub Actions → pytest + lint/build → publish images to GHCR |

## Features

- **Feed of memories** — posts with images, **#hashtags**, and handwritten "polaroid" captions; ❤ reactions, comments, and shares (all optimistic).
- **Schools / communities** — join your school, browse a classmate directory filtered by graduation year, see school memories & photos.
- **Classmate connections** — connect requests, accept/decline, "people you may know" suggestions with mutual counts.
- **Reunions** — events with date/venue/host, **RSVP** (going / maybe / can't go), attendee lists, and amenities.
- **Profiles** — cover photo, class year, school, city, role, interests, and your connections.

## Quickstart

```bash
# 1. env files
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# 2. run everything (dev mode, hot-reload)
docker compose up --build

# 3. load demo data (CBNU + classmates, posts, reunions)
docker compose run --rm backend python scripts/seed.py
```

- App: http://localhost:3000
- API docs (OpenAPI): http://localhost:8000/docs · Health: http://localhost:8000/health
- **Demo login:** `aisha@schoolmate.demo` / `password123`

For the production standalone build (no hot-reload), use the base file only:

```bash
docker compose -f docker-compose.yml up --build
```

### Recommended dev loop (fastest HMR)

```bash
docker compose up postgres backend     # DB + API in Docker
cd frontend && npm install && npm run dev
```

> ⚠️ Never install backend Python deps on the host — the backend is Docker-only (`python:3.12-slim`); `asyncpg` wheels fail on the host's Python 3.14. See `docs/01-environment-setup.md`.

### Tests

```bash
docker compose run --rm backend pytest        # 73 tests
cd frontend && npm run lint && npm run build
```

## CI/CD

Every push & PR to `main` runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

1. **Backend** — spins up Postgres 17 and runs the full pytest suite (73 tests).
2. **Frontend** — `npm ci`, ESLint, `next build`.
3. **Images** — builds the backend + frontend Docker images (validates the Dockerfiles); on `main`, **publishes** them to GHCR:
   - `ghcr.io/vornnaro/schoolmate-backend:latest`
   - `ghcr.io/vornnaro/schoolmate-frontend:latest`

## End-to-end verification

With the stack up and seeded, log in as the demo user and confirm:

1. **Feed** renders posts with class-year badges, hashtags, and a polaroid note; the right rail shows "People you may know" + "Upcoming reunions".
2. **React / comment / share** a post — counts update optimistically and persist on reload.
3. **Avatar menu → Profile** — header + About + Classmates + Memories all load.
4. **School page** (`/school/chungbuk-national-university`) — join, then browse Classmates (filter by year), Memories, Reunions.
5. **Connect** with a suggested classmate — state flips to "Request sent".
6. **Reunion** (`/reunions` → open one) — RSVP going / maybe / can't go; the going-count and attendee list update.
7. **Log out** → cookies cleared → `/feed` redirects to `/login`.

## Documentation

| Doc | Topic |
|---|---|
| [00-project-overview](docs/00-project-overview.md) | scope, stack, decisions |
| [02-architecture](docs/02-architecture.md) | system + repo + Docker design |
| [03-database](docs/03-database.md) | base ERD, models, constraints |
| [04-api](docs/04-api.md) | endpoint contracts (base) |
| [05-auth-flow](docs/05-auth-flow.md) | JWT lifecycle, cookies |
| [06-frontend](docs/06-frontend.md) | pages, components, data layer |
| [08-implementation-phases](docs/08-implementation-phases.md) | build order + verification |

Agentic-coding guides: [`CLAUDE.md`](CLAUDE.md), [`backend/CLAUDE.md`](backend/CLAUDE.md), [`frontend/CLAUDE.md`](frontend/CLAUDE.md).
The `docs/` set describes the original generic social app; the SchoolMate domain (schools, reunions, connections) extends it — see the models, routers, and tests for the current contract.

## Project status

- [x] Phases 1–7 — backend foundation, models, auth, feature APIs, frontend UI
- [x] **SchoolMate** — schools, reunions + RSVP, connections, design system, redesigned login/profile
- [x] Security & correctness review pass + cleanup
- [x] Phase 8 — full dockerization (3-service compose)
- [x] CI/CD — GitHub Actions, images published to GHCR
- [ ] Deferred — direct messaging / reunion discussion, saved posts, profile memories timeline
