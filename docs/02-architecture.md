# 02 — Architecture

## System overview

```
┌──────────────┐  same-origin   ┌─────────────────────┐   Bearer JWT   ┌──────────────┐
│   Browser    │ ─────────────▶ │  Next.js (frontend)  │ ─────────────▶ │   FastAPI    │
│              │  httpOnly      │  · pages/components  │  API_INTERNAL │  (backend)   │
│              │  cookies       │  · /api/auth/* and   │  _URL         │  /api/v1/*   │
│              │                │    /api/proxy/* route│               │              │
└──────────────┘                │    handlers          │               └──────┬───────┘
                                └─────────────────────┘                       │ asyncpg
                                                                       ┌──────▼───────┐
                                                                       │ PostgreSQL 17│
                                                                       └──────────────┘
```

- The browser never holds raw JWTs — they live in httpOnly cookies managed by Next.js route handlers.
- FastAPI is a pure stateless Bearer-token API (clean to test with pytest).
- All three services run under Docker Compose; in dev, the frontend usually runs on the host for fastest HMR.

## Monorepo directory tree

```
Socail-Media-Claude/
├── CLAUDE.md                      # root agentic-coding guide
├── README.md  .gitignore  .env.example
├── docker-compose.yml             # 3 services
├── docker-compose.override.yml    # dev: bind mounts + hot reload (auto-applied)
├── docs/                          # this documentation set
│
├── backend/
│   ├── CLAUDE.md  Dockerfile  .dockerignore  pyproject.toml  .env.example
│   ├── alembic.ini
│   ├── alembic/{env.py, script.py.mako, versions/}
│   ├── app/
│   │   ├── main.py                          # FastAPI app, CORS, routers, /health
│   │   ├── core/
│   │   │   ├── config.py                    # pydantic-settings Settings
│   │   │   ├── security.py                  # bcrypt + JWT encode/decode
│   │   │   └── database.py                  # async engine, AsyncSession, get_db
│   │   ├── models/                          # SQLAlchemy 2.0 Mapped[] style
│   │   │   ├── base.py                      # DeclarativeBase, TimestampMixin, UUID PK
│   │   │   ├── user.py  post.py  comment.py  reaction.py  share.py  refresh_token.py
│   │   ├── schemas/                         # Pydantic v2
│   │   │   ├── auth.py  user.py  post.py  comment.py  reaction.py
│   │   │   └── common.py                    # CursorPage[T] + cursor helpers
│   │   ├── api/
│   │   │   ├── deps.py                      # get_current_user (+ optional variant)
│   │   │   └── routers/
│   │   │       ├── auth.py  users.py  posts.py  comments.py  reactions.py  shares.py
│   │   └── services/feed.py                 # feed UNION query + counts
│   ├── scripts/seed.py
│   └── tests/
│       ├── conftest.py  factories.py
│       └── test_auth.py  test_posts.py  test_comments.py  test_reactions.py  test_shares.py
│
└── frontend/
    ├── CLAUDE.md  Dockerfile  .dockerignore  .env.local.example
    ├── package.json  tsconfig.json  next.config.ts  components.json
    └── src/
        ├── app/
        │   ├── layout.tsx  globals.css
        │   ├── page.tsx                     # redirect → /feed or /login
        │   ├── (auth)/login/page.tsx  (auth)/register/page.tsx
        │   ├── (app)/layout.tsx             # protected layout with Navbar
        │   ├── (app)/feed/page.tsx
        │   ├── (app)/profile/[username]/page.tsx
        │   ├── (app)/post/[id]/page.tsx
        │   └── api/
        │       ├── auth/{login,register,refresh,logout,me}/route.ts   # cookie handlers
        │       └── proxy/[...path]/route.ts                           # cookie→Bearer forwarder
        ├── components/
        │   ├── ui/                          # shadcn-generated (do not hand-edit)
        │   ├── navbar.tsx  feed.tsx  post-card.tsx  post-composer.tsx
        │   ├── comment-list.tsx  comment-form.tsx  reaction-bar.tsx  profile-header.tsx
        ├── lib/{api.ts, auth.ts, query-client.ts, utils.ts}
        ├── hooks/{use-auth.ts, use-feed.ts, use-reactions.ts}
        ├── types/api.ts
        └── middleware.ts                    # route protection
```

Conventions: file-per-resource — a resource (e.g. `post`) has one model file, one schema file, one router file, all named alike.

## Docker design

### `backend/Dockerfile`
- `FROM python:3.12-slim` (host Python 3.14 is never used)
- install deps from `pyproject.toml`
- entrypoint: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`
  (migrations auto-apply on every container start)

### `frontend/Dockerfile`
- `FROM node:24-alpine`, `npm ci`, `npm run build`, run standalone output (`output: 'standalone'` in `next.config.ts`)

### `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:17-alpine
    env_file: .env
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 3s
      retries: 10
    ports: ["5432:5432"]          # exposed for host tooling (psql/pgAdmin)

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      postgres: { condition: service_healthy }
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    environment:
      - API_INTERNAL_URL=http://backend:8000/api/v1
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    depends_on: [backend]
    ports: ["3000:3000"]

volumes:
  pgdata:
```

### `docker-compose.override.yml` (dev hot reload — applied automatically by `docker compose up`)

- **backend**: bind-mount `./backend/app:/app/app` (+ `./backend/alembic`), command override `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **frontend**: bind-mount `./frontend/src`, command override `npm run dev`

### Ports

| Service | URL |
|---|---|
| frontend | http://localhost:3000 |
| backend | http://localhost:8000 (OpenAPI at `/docs`, health at `/health`) |
| postgres | localhost:5432 |
