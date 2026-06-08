# 03 — Database Design (PostgreSQL)

## ERD

```
users 1───N posts            users 1───N refresh_tokens
users 1───N comments         posts 1───N comments
users 1───N reactions        posts 1───N reactions    UNIQUE(user_id, post_id)
users 1───N shares           posts 1───N shares       UNIQUE(user_id, post_id)
```

All FKs to `users`/`posts` are `ON DELETE CASCADE`. All PKs are UUID.

## Base conventions (`app/models/base.py`)

- `class Base(DeclarativeBase)` with `MetaData(naming_convention=...)` so Alembic autogenerate produces stable constraint names (`pk_*`, `fk_*_*_*`, `uq_*_*`, `ix_*_*`, `ck_*_*`).
- `TimestampMixin`:
  - `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())`
  - `updated_at`: same + `onupdate=func.now()`
- UUID PK pattern: `id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- Use SQLAlchemy 2.0 `Mapped[]` / `mapped_column` style ONLY (no legacy `Column =`).

## Tables

### `users`

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| username | String(30) | UNIQUE, INDEX, NOT NULL — stored lowercase; valid `^[a-z0-9_]{3,30}$` (enforced in Pydantic) |
| email | String(255) | UNIQUE, INDEX, NOT NULL — Pydantic `EmailStr` |
| hashed_password | String(128) | NOT NULL — bcrypt |
| display_name | String(80) | NOT NULL — defaults to username at registration |
| bio | Text | NULL |
| avatar_url | Text | NULL |
| is_active | Boolean | NOT NULL DEFAULT true |
| created_at / updated_at | timestamptz | TimestampMixin |

Relationships: `posts`, `comments`, `reactions`, `shares` — `cascade="all, delete-orphan"`, default `lazy="noload"` (load explicitly with `selectinload` where needed; never rely on lazy IO in async).

### `posts`

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| author_id | UUID | FK → users.id ON DELETE CASCADE, INDEX |
| content | Text | NULL |
| image_url | Text | NULL |
| created_at / updated_at | timestamptz | TimestampMixin |

- Table CHECK constraint: `content IS NOT NULL OR image_url IS NOT NULL` (a post must have something).
- Indexes:
  - `ix_posts_author_created (author_id, created_at DESC)` — profile pages
  - `ix_posts_created (created_at DESC, id DESC)` — keyset feed pagination

### `comments`

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| post_id | UUID | FK → posts CASCADE, INDEX |
| author_id | UUID | FK → users CASCADE |
| content | Text | NOT NULL — 1–1000 chars enforced in Pydantic schema |
| created_at / updated_at | timestamptz | TimestampMixin |

Index: `ix_comments_post_created (post_id, created_at)` (ascending — comments list oldest-first).

### `reactions`

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| post_id | UUID | FK → posts CASCADE |
| user_id | UUID | FK → users CASCADE |
| type | ENUM `reaction_type` | NOT NULL — values `LIKE, LOVE, HAHA, WOW, SAD, ANGRY` (native PG enum) |
| created_at | timestamptz | |

- **`UniqueConstraint('user_id', 'post_id', name='uq_reactions_user_post')`** — one reaction per user per post. The unique index also serves the toggle lookup. Changing reaction type = UPDATE the row, not a second insert.

### `shares`

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| post_id | UUID | FK → posts CASCADE |
| user_id | UUID | FK → users CASCADE |
| created_at | timestamptz | |

- **`UniqueConstraint('user_id', 'post_id', name='uq_shares_user_post')`** — makes repost idempotent (catch `IntegrityError` → treat as already-shared, do NOT pre-check with SELECT).
- Index `ix_shares_created (created_at DESC)` — feed UNION ordering.

### `refresh_tokens`

| column | type | constraints |
|---|---|---|
| jti | UUID | PK (the JWT ID claim) |
| user_id | UUID | FK → users CASCADE, INDEX |
| expires_at | timestamptz | NOT NULL |
| revoked | Boolean | NOT NULL DEFAULT false |
| created_at | timestamptz | |

Used for refresh rotation + reuse (theft) detection — see [05-auth-flow.md](05-auth-flow.md). Cleanup of expired rows is a future extension (volume is trivial).

## Design decisions

1. **Repost model (v1)**: the `shares` table is the source of truth. The feed query is a UNION of original posts and shares-joined-to-posts, ordered by event time (post `created_at` or share `created_at`). Quote-repost via a `posts.original_post_id` self-FK is a **documented future extension — do not build in v1**.
2. **Images (v1)**: `image_url` is a plain URL string supplied by the client. Multipart upload + static `/uploads` mount is a future extension.
3. **Counts**: reaction/comment/share counts are computed with correlated subqueries (`func.count`) in the feed/post queries. No denormalized counter columns in v1.

## Migrations (Alembic)

- Async-compatible `alembic/env.py` (use the `async_engine_from_config` template) importing `Base.metadata` from `app.models`.
- All model modules must be imported in `app/models/__init__.py` so autogenerate sees them.
- Workflow (always inside the container):
  ```
  docker compose run --rm backend alembic revision --autogenerate -m "initial schema"
  docker compose run --rm backend alembic upgrade head
  ```
- The backend container entrypoint also runs `alembic upgrade head` on start.
- Gotcha: native PG enums — when adding enum values later, autogenerate does NOT detect them; hand-write `ALTER TYPE`.
