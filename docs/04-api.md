# 04 — API Contracts

Base path: **`/api/v1`** · JSON only · Auth: `Authorization: Bearer <access_token>`.

Error shape (FastAPI default): `{"detail": "message"}` (Pydantic validation errors return the standard 422 list).

| Status | Meaning |
|---|---|
| 400 | business-rule violation |
| 401 | missing/invalid/expired token, bad credentials |
| 403 | authenticated but not the owner / inactive |
| 404 | resource not found |
| 409 | conflict (duplicate username/email) |
| 422 | request validation failed |

## Endpoint summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /auth/register | – | create account, return token pair |
| POST | /auth/login | – | verify creds, return token pair |
| POST | /auth/refresh | refresh token | rotate token pair |
| POST | /auth/logout | refresh token | revoke refresh token |
| GET | /auth/me | access | current user |
| GET | /users/{username} | optional | public profile + post_count |
| PATCH | /users/me | access | update profile |
| GET | /users/{username}/posts | optional | user's posts (cursor) |
| GET | /posts | optional | global feed (cursor) |
| POST | /posts | access | create post |
| GET | /posts/{id} | optional | single post |
| PATCH | /posts/{id} | access (author) | edit own post |
| DELETE | /posts/{id} | access (author) | delete own post |
| GET | /posts/{id}/comments | optional | comments (cursor, oldest-first) |
| POST | /posts/{id}/comments | access | add comment |
| DELETE | /comments/{id} | access (author) | delete own comment |
| PUT | /posts/{id}/reactions | access | set/toggle reaction |
| DELETE | /posts/{id}/reactions | access | remove own reaction |
| GET | /posts/{id}/reactions | optional | counts + my reaction |
| POST | /posts/{id}/shares | access | repost (idempotent) |
| DELETE | /posts/{id}/shares | access | un-share |

## Auth endpoints

### POST `/auth/register` → 201
Request:
```json
{"username": "naro", "email": "naro@example.com", "password": "secret123", "display_name": "Naro"}
```
- `username`: `^[a-z0-9_]{3,30}$` (lowercased server-side) · `password`: min 8 chars · `display_name` optional (defaults to username).

Response 201:
```json
{
  "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer",
  "user": {"id": "uuid", "username": "naro", "display_name": "Naro", "email": "naro@example.com",
           "bio": null, "avatar_url": null, "created_at": "2026-06-06T10:00:00Z"}
}
```
Errors: 409 `"Username already taken"` / `"Email already registered"`.

### POST `/auth/login` → 200
Request: `{"username_or_email": "naro", "password": "secret123"}`
Response: same shape as register. Error: 401 `"Incorrect username or password"` — never reveal which field was wrong.

### POST `/auth/refresh` → 200
Request: `{"refresh_token": "eyJ..."}`
Response: `{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}` — NEW pair; old refresh jti revoked.
Errors: 401 if expired/invalid/revoked. **Reuse of an already-rotated token revokes ALL the user's refresh tokens** (theft detection) and returns 401.

### POST `/auth/logout` → 204
Request: `{"refresh_token": "eyJ..."}`. Revokes that jti.

### GET `/auth/me` → 200 `UserOut`

## User endpoints

`UserOut`: `{id, username, display_name, email, bio, avatar_url, created_at}` (email only included for self via `/auth/me`; public profile omits it).

- **GET `/users/{username}`** → 200 `UserOut` (no email) + `"post_count": 12` · 404.
- **PATCH `/users/me`** — `{display_name?, bio?, avatar_url?}` (partial, `exclude_unset`) → 200 `UserOut`.
- **GET `/users/{username}/posts`** — `?limit=20&cursor=` → `CursorPage<PostOut>`.

## Posts

`AuthorMini`: `{id, username, display_name, avatar_url}`

`PostOut` (canonical shape, used in feed, profile, single post):
```json
{
  "id": "uuid",
  "author": {"id": "uuid", "username": "naro", "display_name": "Naro", "avatar_url": null},
  "content": "Hello world!", "image_url": null,
  "created_at": "...", "updated_at": "...",
  "reaction_counts": {"LIKE": 3, "LOVE": 1},
  "my_reaction": "LIKE",
  "comment_count": 2,
  "share_count": 1,
  "shared_by_me": false,
  "shared_by": null
}
```
- `my_reaction` / `shared_by_me` → `null` / `false` for unauthenticated requests.
- For feed items that are reposts: `shared_by = {"username": "...", "display_name": "...", "shared_at": "..."}`.

- **GET `/posts`** — optional auth, `?limit=20&cursor=` → `{"items": [PostOut], "next_cursor": "...", "has_more": true}`. Feed = original posts ∪ reposts, ordered by event time desc.
- **POST `/posts`** — `{content?, image_url?}`; Pydantic model validator requires at least one → 201 `PostOut`.
- **GET `/posts/{id}`** → 200 `PostOut` · 404.
- **PATCH `/posts/{id}`** — author only (403), `{content?, image_url?}` → 200.
- **DELETE `/posts/{id}`** — author only → 204 (cascades comments/reactions/shares).

## Comments

`CommentOut`: `{id, post_id, author: AuthorMini, content, created_at}`

- **GET `/posts/{id}/comments`** — `?limit=20&cursor=`, **oldest-first** → `CursorPage<CommentOut>`.
- **POST `/posts/{id}/comments`** — `{content}` (1–1000 chars) → 201 `CommentOut` · 404 if post missing.
- **DELETE `/comments/{id}`** — comment author only → 204.

## Reactions

Types: `LIKE | LOVE | HAHA | WOW | SAD | ANGRY`.

- **PUT `/posts/{id}/reactions`** — body `{"type": "LIKE"}`.
  Semantics (single endpoint, toggle/upsert):
  - no existing reaction → insert
  - same type as existing → **delete** (toggle off)
  - different type → update in place
  Response 200: `{"my_reaction": "LIKE" | null, "reaction_counts": {"LIKE": 4}}`
- **DELETE `/posts/{id}/reactions`** → 200 same response shape.
- **GET `/posts/{id}/reactions`** — optional auth → 200 `{"reaction_counts": {...}, "my_reaction": "..." | null}`.

## Shares

- **POST `/posts/{id}/shares`** → 201 `{"share_count": 2, "shared_by_me": true}`.
  Duplicate share → 200 with the same body (idempotent — catch the unique-constraint `IntegrityError`, don't pre-check). Sharing your own post is allowed in v1.
- **DELETE `/posts/{id}/shares`** → 200 `{"share_count": 1, "shared_by_me": false}`.

## Cursor pagination (shared helper)

Location: `app/schemas/common.py` (page model + encode/decode) and used by `services/feed.py`.

- Cursor = `base64url(json({"t": "<ISO created_at>", "id": "<uuid>"}))` — opaque to clients.
- Query pattern (descending feeds):
  `WHERE (created_at, id) < (:t, :id) ORDER BY created_at DESC, id DESC LIMIT :limit + 1`
- Fetch `limit + 1` rows; if you got the extra row → `has_more = true` and `next_cursor` encodes the **last returned** item; drop the extra row.
- Comments use the same helper ascending (`>` and `ASC`).
- Response model: `CursorPage[T] = {"items": [...], "next_cursor": str | null, "has_more": bool}`.
- `limit` query param: default 20, max 50.

Why keyset (not offset): an infinite-scroll feed where new posts arrive constantly — offset pagination would skip/duplicate items between pages.
