# 08 — Implementation Phases

Execute in order. Every phase ends with its **Verify** step passing before moving on. Reference docs are listed per phase — an agent should be able to implement each phase from this file + the referenced doc alone.

> Phase 0 (this documentation set + repo init) is complete when these docs exist and the repo has its initial commit.

## Phase 1 — Backend foundation
**Docs**: [02-architecture.md](02-architecture.md), [01-environment-setup.md](01-environment-setup.md)

- `backend/pyproject.toml` — runtime deps: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic`, `pydantic-settings`, `pyjwt`, `bcrypt`, `email-validator`, `python-multipart`; dev deps: `pytest`, `pytest-asyncio`, `httpx`, `asgi-lifespan`, `ruff`.
- `app/core/config.py` (pydantic-settings reading the env vars), `app/core/database.py` (async engine, sessionmaker, `get_db` dependency), `app/main.py` (FastAPI app, CORS from `CORS_ORIGINS`, `/health` → `{"status":"ok"}`).
- `backend/Dockerfile` (`python:3.12-slim`), `.dockerignore`.
- `docker-compose.yml` with `postgres` + `backend` (+ override file for `--reload`).

**Verify**: `docker compose up postgres backend --build` → `GET http://localhost:8000/health` = 200; `/docs` renders.

## Phase 2 — Models + migrations
**Docs**: [03-database.md](03-database.md)

- All 6 models + `base.py` exactly per spec; import everything in `models/__init__.py`.
- Alembic init with async template; first `revision --autogenerate -m "initial schema"`.
- Add `alembic upgrade head` to the container entrypoint.

**Verify**: `docker compose run --rm backend alembic upgrade head`; then
`docker compose exec postgres psql -U socialhub -c "\dt"` shows all 6 tables; `\dT+ reaction_type` shows the enum; unique constraints visible in `\d reactions` / `\d shares`.

## Phase 3 — Authentication
**Docs**: [05-auth-flow.md](05-auth-flow.md), [04-api.md](04-api.md) (auth section), [07-testing.md](07-testing.md)

- `core/security.py`, `schemas/auth.py`, `api/routers/auth.py` (register/login/refresh/logout/me), `api/deps.py`.
- Set up `tests/conftest.py` per the testing doc, then `tests/test_auth.py`.

**Verify**: `docker compose run --rm backend pytest tests/test_auth.py -x` — all green, including rotation + reuse-detection cases.

## Phase 4 — Core features (posts/comments/reactions/shares)
**Docs**: [04-api.md](04-api.md), [03-database.md](03-database.md), [07-testing.md](07-testing.md)

- `schemas/common.py` cursor helper first (everything reuses it).
- Routers + schemas for posts, comments, reactions, shares; `services/feed.py` (UNION query + count subqueries + `my_reaction`/`shared_by_me` personalization).
- Tests: `test_posts.py`, `test_comments.py`, `test_reactions.py`, `test_shares.py`.

**Verify**: full `docker compose run --rm backend pytest` green; manual smoke via `/docs` (register → post → react → comment → share → feed shows counts).

## Phase 5 — Frontend scaffold
**Docs**: [06-frontend.md](06-frontend.md) (scaffold section)

- Run the scaffold commands; add Providers (React Query + next-themes); `lib/api.ts`, `lib/utils.ts`, `types/api.ts`; `output: 'standalone'` in next.config.

**Verify**: `npm run dev` renders a styled placeholder page; `npm run lint` passes; a temporary call to `/api/proxy/posts`... (proxy not built yet — instead hit `http://localhost:8000/health` directly) returns 200.

## Phase 6 — Auth UI + protection
**Docs**: [05-auth-flow.md](05-auth-flow.md) (Next.js sections), [06-frontend.md](06-frontend.md)

- Route handlers: `api/auth/{login,register,refresh,logout,me}` + `api/proxy/[...path]`.
- Login/register pages with zod validation; `middleware.ts`; `hooks/use-auth.ts`; navbar logout.

**Verify** (browser): register → lands on `/feed` · devtools shows both cookies httpOnly · logged-out `/feed` redirects to `/login` · logged-in `/login` redirects to `/feed` · temporarily set `ACCESS_TOKEN_EXPIRE_MINUTES=1` and confirm a data call after expiry silently refreshes and succeeds.

## Phase 7 — Feed & feature UI
**Docs**: [06-frontend.md](06-frontend.md), [04-api.md](04-api.md)

- Navbar, Feed (useInfiniteQuery + IntersectionObserver), PostComposer, PostCard, ReactionBar (optimistic), ShareButton, post detail page with comments, ProfileHeader + edit dialog, dark-mode toggle, skeletons + toasts.

**Verify** (browser, full loop): create post → appears top of feed · react like → love → off (optimistic, survives reload) · comment from /post/[id] · share (banner shows on repost) · profile page edit bio · infinite scroll past 20 posts · logout.

## Phase 8 — Full dockerization
**Docs**: [02-architecture.md](02-architecture.md) (Docker section)

- `frontend/Dockerfile` (standalone build), add `frontend` service to compose, finalize `docker-compose.override.yml` hot-reload for both services.

**Verify**: clean `docker compose up --build` (all 3 services) → full browser loop at `localhost:3000` · edit a backend file → uvicorn autoreloads · edit a frontend file → HMR (dev override).

## Phase 9 — Polish & final pass
**Docs**: [07-testing.md](07-testing.md), this file

- `backend/scripts/seed.py` — 3 users, ~15 posts, comments/reactions/shares spread around (run: `docker compose run --rm backend python scripts/seed.py`).
- Finalize README; ensure `.env.example` files are accurate.

**Verify**: final E2E checklist below.

---

## Final end-to-end verification checklist

1. Clean clone → copy `.env.example → .env`, `frontend/.env.local.example → frontend/.env.local`
2. `docker compose up --build` → postgres healthy → migrations auto-run → all 3 up
3. `:8000/health` 200 · `:8000/docs` interactive · `:3000` loads
4. Register → redirected to /feed · cookies httpOnly in devtools
5. Create post (text + image URL) → top of feed
6. React: like → love → off — counts update optimistically, persist on reload
7. Comment → thread on /post/[id] · count on the card updates
8. Share → count++, repost shows "shared by" banner · re-share idempotent
9. /profile/username → header renders, edit bio persists, posts listed
10. Logout → cookies cleared → /feed redirects to /login
11. `docker compose run --rm backend pytest` → entire suite green
