# 01 — Environment Setup

## Required tools (Windows 11)

| Tool | Needed for | Verified on this machine |
|---|---|---|
| **Docker Desktop** (WSL2 backend) | PostgreSQL, FastAPI backend, full-stack compose | ✅ Docker 29, Compose v5 |
| **Node.js 20+** | Next.js dev server, npm/npx | ✅ v24.14 |
| **Git** | version control | ✅ 2.53 |
| VS Code extensions (optional) | Python, Ruff, Tailwind CSS IntelliSense, ESLint | — |

## ⚠️ Python 3.14 warning (important)

The host machine has **Python 3.14**, which is too new: `asyncpg` (the async PostgreSQL driver) may not ship prebuilt wheels for it and will fail to compile on Windows.

**Rule: never install backend dependencies on the host.** The backend runs exclusively inside Docker using the `python:3.12-slim` image, so the host Python version is irrelevant.

If you ever *must* run the backend on the host, install Python 3.12 side-by-side and create the venv with `py -3.12 -m venv .venv` — but the supported workflow is Docker.

## Recommended dev workflow

```
docker compose up postgres backend     # DB + API in Docker (hot reload via override file)
cd frontend && npm run dev             # Next.js on host (fastest HMR)
```

Full-stack in Docker (`docker compose up`) is for final verification / demo.

## Environment files

### Root `.env` (copy from `.env.example`) — consumed by docker-compose

```env
POSTGRES_USER=socialhub
POSTGRES_PASSWORD=devpassword
POSTGRES_DB=socialhub
DATABASE_URL=postgresql+asyncpg://socialhub:devpassword@postgres:5432/socialhub
JWT_SECRET_KEY=change-me-dev-only
JWT_REFRESH_SECRET_KEY=change-me-dev-only-2
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
```

> Note: inside the Docker network the DB host is `postgres` (service name). From the host it is `localhost:5432`.

### `backend/.env` (copy from `backend/.env.example`)

Same backend variables, but `DATABASE_URL` uses host `localhost` — only used if running on the host with Python 3.12 (not the supported path).

### `frontend/.env.local` (copy from `frontend/.env.local.example`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
API_INTERNAL_URL=http://localhost:8000/api/v1
```

- `NEXT_PUBLIC_API_URL` — browser → backend URL (only used for direct calls; most traffic goes through the Next proxy route).
- `API_INTERNAL_URL` — Next.js route handlers / server components → backend. On the host this is `http://localhost:8000/api/v1`; **inside Docker Compose it is overridden to `http://backend:8000/api/v1`** by the compose file.

## First-time setup checklist

1. `git init` in the project root (if not already a repo).
2. Copy the three env example files to their live names (`.env`, `frontend/.env.local`).
3. `docker compose up postgres backend --build` → wait for healthcheck → open `http://localhost:8000/docs`.
4. `cd frontend && npm install && npm run dev` → open `http://localhost:3000`.

## Secrets policy

- `.env*` files are gitignored; only `*.example` files are committed.
- Dev JWT secrets are placeholders; generate real ones for any non-local deployment: `openssl rand -hex 32` (or PowerShell: `-join ((48..57)+(97..102) | Get-Random -Count 64 | % {[char]$_})`).
