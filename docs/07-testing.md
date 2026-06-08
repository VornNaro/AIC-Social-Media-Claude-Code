# 07 — Testing Strategy (pytest)

## Stack

`pytest` · `pytest-asyncio` (`asyncio_mode = "auto"` in pyproject) · `httpx` (`ASGITransport` — no live server needed) · `asgi-lifespan`.

## Test database — real PostgreSQL, not SQLite

A separate **`socialhub_test`** database on the same Postgres container.

- Why real PG: native ENUM (`reaction_type`), `ON DELETE CASCADE`, unique-constraint behavior, and timestamptz must behave exactly as production. **SQLite is explicitly rejected** (dialect mismatch would silently change semantics).
- Why not testcontainers: Docker-in-Docker friction on Windows; the compose Postgres is already there.
- `conftest.py` creates the test DB if absent (connect to the default DB with autocommit → `CREATE DATABASE socialhub_test`).

## `tests/conftest.py` design

```
session scope:
  - test engine → create socialhub_test if missing → Base.metadata.create_all once
per test:
  - open connection, BEGIN outer transaction
  - AsyncSession bound to that connection
  - app.dependency_overrides[get_db] = the test session
  - AsyncClient(transport=ASGITransport(app), base_url="http://test")
  - teardown: ROLLBACK  → every test starts from a clean DB, fast
```

Fixtures:

| Fixture | Provides |
|---|---|
| `client` | unauthenticated `AsyncClient` |
| `db` | the test `AsyncSession` |
| `user` | a registered user (via the real `/auth/register` endpoint) + its tokens |
| `auth_client` | `AsyncClient` with `Authorization: Bearer <user's access>` |
| `other_auth_client` | a second user's client (ownership tests) |
| `post` | a post created by `user` |

`tests/factories.py`: tiny helpers `make_user(client, n)` / `make_post(auth_client, **kw)` — no factory-boy needed at this scope.

## Running

```bash
docker compose run --rm backend pytest                         # full suite
docker compose run --rm backend pytest tests/test_auth.py -x   # one file, stop at first failure
docker compose run --rm backend pytest tests/test_auth.py::test_refresh_rotation
```

(Requires the `postgres` service running: `docker compose up -d postgres`.)

## Test case matrix

### `test_auth.py`
- register → 201, response has token pair + user; password absent from response
- duplicate username → 409 · duplicate email → 409 · password < 8 chars → 422 · bad username pattern → 422
- login with username → 200 · with email → 200 · wrong password → 401 (generic message)
- `GET /auth/me` with token → 200 · without → 401 (or 403 from HTTPBearer) · garbage token → 401
- refresh → 200 new pair; **old refresh token now 401** (rotation)
- **reuse of a rotated refresh token → 401 AND all the user's refresh tokens revoked** (subsequent refresh with the newest token also 401)
- logout → 204; refresh with that token → 401

### `test_posts.py`
- create text-only / image-only / both → 201 · neither → 422
- feed pagination: create 25 posts → page 1 has 20 + `has_more` + cursor → page 2 has 5, no overlap/gap, descending order stable
- get by id → 200 · unknown id → 404
- patch own → 200, content updated · patch other's → 403
- delete own → 204; its comments/reactions/shares gone (cascade) · delete other's → 403
- unauthenticated feed → 200 with `my_reaction: null`, `shared_by_me: false`

### `test_comments.py`
- add → 201, `comment_count` on post increments
- content 1000 chars → 201 · 1001 → 422 · empty → 422
- list: ascending order, cursor works on >20 comments
- delete own → 204 · other's → 403 · comment on missing post → 404

### `test_reactions.py`
- PUT LIKE → 200, counts `{"LIKE": 1}`, `my_reaction: "LIKE"`
- PUT LIKE again → toggled off: `my_reaction: null`, counts empty
- PUT LIKE then PUT LOVE → swapped: counts `{"LOVE": 1}` only — DB still has exactly 1 row (unique constraint honored)
- two users react → counts aggregate to 2; each sees their own `my_reaction`
- DELETE → removed · invalid type → 422

### `test_shares.py`
- share → 201, `share_count: 1`, `shared_by_me: true`
- duplicate share → 200 idempotent, count still 1
- unshare → 200, count 0
- shared post appears in the OTHER user's feed view with `shared_by` populated

## Conventions

- Tests never `commit()` directly on `db` — go through the API; the rollback fixture cleans up.
- Each test is independent — no ordering assumptions.
- Assert response **shapes** (keys present) as well as values, since the frontend types mirror them.
