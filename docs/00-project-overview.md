# 00 — Project Overview

## What we are building

**Social Hub** — a social media web application where users can register, manage a profile, create posts, comment, react, and share (repost), presented in a modern feed UI (sticky navbar, centered feed of post cards, post composer, profile pages). UI reference: the user's "Social Hub" Replit app.

## Tech stack (confirmed decisions)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router, TypeScript), Tailwind CSS, shadcn/ui, TanStack React Query |
| Backend | Python FastAPI, SQLAlchemy 2.0 (async), Alembic migrations, Pydantic v2 |
| Database | PostgreSQL 17 |
| Auth | JWT — access token (15 min) + refresh token (7 days) with rotation; bcrypt password hashing; httpOnly cookies set by Next.js route handlers |
| Deployment | Docker Compose (local) — 3 services: `postgres`, `backend`, `frontend` |
| Testing | pytest (backend) against a real PostgreSQL test database |

## Features (v1 scope)

1. **Authentication** — register, login, logout, token refresh with rotation + reuse detection.
2. **User profiles** — public profile page (`/profile/[username]`), editable display name / bio / avatar URL.
3. **Posts** — text + optional image URL; edit/delete own posts; global feed with cursor-based infinite scroll.
4. **Comments** — add/list/delete on posts.
5. **Reactions** — one reaction per user per post, 6 types (LIKE, LOVE, HAHA, WOW, SAD, ANGRY), toggle semantics.
6. **Shares (reposts)** — idempotent repost; shared posts appear in the feed with a "shared by" banner.

## Explicitly OUT of v1 scope (documented future extensions)

- Quote-reposts (`posts.original_post_id`) — shares table only in v1
- File/image uploads — `image_url` strings only in v1
- Follows/friends graph, notifications, DMs, WebSockets
- Redis, Celery, microservices — single FastAPI app only
- Denormalized counter columns — counts computed by query

## Machine environment (verified 2026-06-06)

| Tool | Version | Status |
|---|---|---|
| Node.js | v24.14.0 | ✅ |
| Git | 2.53 | ✅ |
| Docker + Compose | 29 / v5 | ✅ |
| Python (host) | 3.14 | ⚠️ too new for `asyncpg` wheels on Windows |

> **Critical constraint:** the backend is **Docker-only** (`python:3.12-slim`). Never install backend Python dependencies on the host. See [01-environment-setup.md](01-environment-setup.md).

## Document map

| Doc | Covers | Implements phase |
|---|---|---|
| [01-environment-setup.md](01-environment-setup.md) | tools, env files | 0 |
| [02-architecture.md](02-architecture.md) | monorepo tree, Docker/Compose design | 1, 8 |
| [03-database.md](03-database.md) | ERD, model specs, constraints | 2 |
| [04-api.md](04-api.md) | endpoint contracts, pagination | 3, 4 |
| [05-auth-flow.md](05-auth-flow.md) | token lifecycle, cookies, route protection | 3, 6 |
| [06-frontend.md](06-frontend.md) | pages, components, React Query design | 5, 6, 7 |
| [07-testing.md](07-testing.md) | pytest strategy, test matrix | 3, 4, 9 |
| [08-implementation-phases.md](08-implementation-phases.md) | execution order + verification | all |
