# Backend (FastAPI) — Agent Guide

Async FastAPI app under `app/`. Spec docs: `../docs/03-database.md`, `../docs/04-api.md`, `../docs/05-auth-flow.md`, `../docs/07-testing.md`.

## Layering

```
api/routers/*  →  schemas/* (validate in/out)  →  models/* + services/*  →  core/database.py
```

- Routers stay thin: parse/validate via Pydantic schema → call query logic → return schema. Nontrivial queries (feed UNION, counts) live in `services/`.
- `api/deps.py` is the ONLY auth entry point — routers depend on `get_current_user` / `get_current_user_optional`; never decode JWTs in a router.
- `core/security.py` is the only place that touches `pyjwt`/`bcrypt`.

## Conventions

- SQLAlchemy 2.0 declarative: `Mapped[]` + `mapped_column` only; relationships default `lazy="noload"` — fetch explicitly with `selectinload`; never trigger lazy IO in async.
- Pydantic v2: `model_config = ConfigDict(from_attributes=True)` for ORM reads; partial updates via `model_dump(exclude_unset=True)`.
- Cursor pagination: ALWAYS reuse the helper in `app/schemas/common.py` (`CursorPage[T]`, encode/decode). Don't write ad-hoc offset pagination.
- Unique-constraint handling (`reactions`, `shares`): attempt the write and catch `IntegrityError` → treat as toggle/idempotent success. No SELECT-then-INSERT races.

## New endpoint checklist

1. Schema(s) in `app/schemas/<resource>.py`
2. Route in `app/api/routers/<resource>.py` (correct status codes per `docs/04-api.md`)
3. Router registered in `app/main.py` (`include_router`, prefix `/api/v1`)
4. Tests in `tests/test_<resource>.py` (happy path + auth + ownership + validation)
5. If models changed: `docker compose run --rm backend alembic revision --autogenerate -m "..."` → review the generated migration → `upgrade head`

## Tests

- Run: `docker compose run --rm backend pytest` (postgres service must be up).
- conftest gives per-test transaction rollback — **never call `commit()` on the `db` fixture or create data outside the API/fixtures**; it will leak between tests.
- Test DB is `socialhub_test` (real Postgres — keeps ENUM/cascade semantics). Don't switch to SQLite.
- Fixtures available: `client`, `auth_client`, `other_auth_client`, `user`, `post`, `db` (see `tests/conftest.py`).

## Gotchas

- Migrations and pytest run INSIDE the container — host Python is 3.14 and unsupported.
- `decode_token` must verify the `type` claim (`access` vs `refresh`) — mixing them is a security bug with a test.
- Refresh reuse (unknown/revoked jti) ⇒ revoke ALL the user's refresh tokens, then 401.
- Login error is generic ("Incorrect username or password") — never reveal whether username or password failed.
