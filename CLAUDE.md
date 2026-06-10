# SchoolMate — Agent Guide

Monorepo **SchoolMate** — a nostalgic alumni reunion network (built on a generic social-app base, then extended with schools, classmate connections, and reunions): **Next.js 16** (`frontend/`, port 3000) · **FastAPI** (`backend/`, port 8000, path `/api/v1`) · **PostgreSQL 17** (Docker). Auth = JWT access+refresh pair with rotation; browser stores tokens in **httpOnly cookies set by Next.js route handlers**; FastAPI itself is a pure stateless Bearer API.

Full specification lives in `docs/` (00-overview … 08-phases). **Read the doc for the phase you're implementing before writing code.** Implementation order and per-phase verification: `docs/08-implementation-phases.md`.

## Commands

```bash
# recommended dev loop
docker compose up postgres backend        # API + DB in Docker (hot reload via override)
cd frontend && npm run dev                # Next.js on host (fastest HMR)

docker compose up --build                 # full stack (final verification/demo)

# tests (backend only; postgres service must be up)
docker compose run --rm backend pytest
docker compose run --rm backend pytest tests/test_auth.py::test_refresh_rotation -x

# migrations — ALWAYS inside the container
docker compose run --rm backend alembic revision --autogenerate -m "..."
docker compose run --rm backend alembic upgrade head

# lint
docker compose run --rm backend ruff check app
cd frontend && npm run lint

# shadcn component
cd frontend && npx shadcn@latest add <name>
```

## Conventions

- **Backend**: SQLAlchemy 2.0 `Mapped[]`/`mapped_column` only (no legacy style) · Pydantic v2 (`model_config`, `model_validate`) · async everywhere — never sync DB calls, never rely on lazy-loading in async (use `selectinload`) · file-per-resource: `models/post.py` + `schemas/post.py` + `api/routers/post s.py` share the name · cursor pagination helper in `app/schemas/common.py` — reuse it, don't reinvent.
- **Frontend**: data access ONLY via React Query hooks in `src/hooks/`; raw `fetch` ONLY inside `src/lib/api.ts` · types in `src/types/api.ts` mirror backend schemas, snake_case preserved · shadcn components live in `src/components/ui/` — regenerate, never hand-edit.

## Gotchas

- **Host Python is 3.14 — NEVER install backend deps on the host.** Everything backend runs in Docker (`python:3.12-slim`); `asyncpg` wheels fail on host 3.14/Windows.
- `DATABASE_URL` host is `postgres` inside compose, `localhost` from the host.
- httpOnly cookies mean client JS can never read tokens — all browser data calls go through `/api/proxy/[...path]`, auth calls through `/api/auth/*`. Don't try to attach Bearer headers in client components.
- `reactions` and `shares` both have `UNIQUE(user_id, post_id)` — handle `IntegrityError` as toggle/idempotent-success; do NOT pre-check with SELECT.
- Refresh-token reuse (revoked/unknown jti) must revoke ALL of that user's refresh tokens — it's a theft signal, and there's a test for it.
- Alembic autogenerate does not detect added PG enum values — hand-write `ALTER TYPE` migrations for those.

## Scope guardrails

**In scope and built (SchoolMate domain):** schools/communities + membership, classmate **connections** (request / accept / decline, suggestions), and **reunions** with RSVPs (going / maybe / declined) — on top of the base posts / comments / reactions / shares. Posts carry `tags` (#hashtags) + a handwritten `note`; users carry school / graduation_year / city / role / cover / interests.

**Deferred — do not build unprompted:** direct messaging / reunion discussion threads, saved/bookmarked posts, the profile "memories" timeline. (Connection requests currently allow any user, not just same-school — an open product decision.)

**Out of scope:** Redis, Celery, microservices, WebSockets, push notifications, file uploads (images stay URL strings). Quote-repost (`original_post_id`) remains a future extension.

## Specialist skills (`.claude/skills/`)

Eight project-scoped skills installed from `alirezarezvani/claude-skills` (engineering-team). Invoke the matching skill when working on its phase:

| Skill | Use during |
|---|---|
| `senior-architect` | architecture sanity-checks; future extensions (quote-repost, uploads) |
| `senior-backend` | Phases 1–4 — FastAPI foundation, models, auth, feature APIs |
| `tdd-guide` | Phases 3–4 — write pytest tests before/alongside each endpoint |
| `senior-qa` | Phases 3, 4, 9 — coverage strategy, edge cases |
| `senior-security` | after Phase 3 — review JWT rotation, cookie flags, bcrypt usage |
| `senior-frontend` | Phases 5–7 — Next.js scaffold, components, React Query |
| `senior-devops` | Phase 8 — Docker Compose, hot-reload, healthchecks |
| `code-reviewer` | end of EVERY phase — review the diff before moving on |

Note: some skill examples reference Node/Express — this project's backend is FastAPI/Python; apply the patterns, not the literal stack. Their bundled `scripts/` are optional helpers, not part of the build.

## Subsystem guides

- `backend/CLAUDE.md` — layering, auth deps, test conventions, new-endpoint checklist
- `frontend/CLAUDE.md` — route groups, query keys, optimistic-update pattern
