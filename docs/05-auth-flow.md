# 05 — Authentication Flow

## Token design

| Token | Lifetime | Signed with | Payload |
|---|---|---|---|
| Access JWT | 15 min | `JWT_SECRET_KEY` | `{sub: user_id, type: "access", exp, iat}` |
| Refresh JWT | 7 days | `JWT_REFRESH_SECRET_KEY` | `{sub: user_id, type: "refresh", jti, exp, iat}` |

- Algorithm HS256 (`pyjwt`). Passwords hashed with `bcrypt`.
- Every refresh token's `jti` has a row in the `refresh_tokens` table (`jti, user_id, expires_at, revoked`).

`app/core/security.py` exports:
- `hash_password(plain) -> str` / `verify_password(plain, hashed) -> bool`
- `create_access_token(user_id) -> str`
- `create_refresh_token(user_id) -> tuple[token, jti, expires_at]`
- `decode_token(token, expected_type) -> payload` — raises a single `CredentialsError` on any failure (bad sig, expired, wrong type)

## Sequences (FastAPI side)

### Register / Login
1. Validate input (register: 409 on duplicate username/email; login: verify bcrypt, generic 401).
2. Create access token + refresh token; INSERT `refresh_tokens` row.
3. Return `{access_token, refresh_token, token_type, user}`.

### Refresh (rotation + theft detection)
1. Decode refresh JWT (signature, expiry, `type == "refresh"`). Fail → 401.
2. SELECT `refresh_tokens` by `jti`:
   - **not found or `revoked = true`** → token reuse detected (possible theft):
     `UPDATE refresh_tokens SET revoked = true WHERE user_id = :uid` (revoke ALL sessions) → 401.
   - else → set this row `revoked = true`, issue a NEW pair, INSERT new jti row → 200.

### Logout
Revoke the presented refresh jti → 204. (The Next.js handler also clears cookies.)

## Browser storage — httpOnly cookies via Next.js

**Decision**: tokens are stored in httpOnly cookies that browser JavaScript can never read (XSS-safe). FastAPI stays a pure stateless Bearer API (trivially testable with pytest). All cookie logic lives in Next.js route handlers.

### Cookies

| Cookie | Flags | maxAge |
|---|---|---|
| `access_token` | httpOnly, SameSite=Lax, Path=/ | 15 min |
| `refresh_token` | httpOnly, SameSite=Lax, **Path=/api/auth** | 7 days |

Add `Secure` in production. The refresh cookie's narrow Path means it is only sent to the auth route handlers.

### Next.js route handlers (`src/app/api/`)

| Handler | Does |
|---|---|
| `auth/register/route.ts` | forward body → FastAPI `/auth/register` → set both cookies → return `{user}` |
| `auth/login/route.ts` | same for `/auth/login` |
| `auth/refresh/route.ts` | read `refresh_token` cookie → FastAPI `/auth/refresh` → re-set both cookies → 200, or clear cookies + 401 |
| `auth/logout/route.ts` | read refresh cookie → FastAPI `/auth/logout` → clear both cookies → 204 |
| `auth/me/route.ts` | read access cookie → FastAPI `/auth/me` with Bearer → return user (401 passthrough) |
| **`proxy/[...path]/route.ts`** | generic data forwarder: copy `access_token` cookie into `Authorization: Bearer`, forward method/body/query to `${API_INTERNAL_URL}/<path>`, stream response back |

All handlers call FastAPI at `API_INTERNAL_URL` (`http://backend:8000/api/v1` in Docker, `http://localhost:8000/api/v1` on host).

### Request flow (browser)

```
browser ──POST /api/auth/login──▶ Next handler ──▶ FastAPI /auth/login
        ◀─ Set-Cookie ×2 + {user} ─┘

browser ──GET /api/proxy/posts──▶ proxy handler (cookie→Bearer) ──▶ FastAPI /posts
        ◀───────── JSON ──────────┘
```

Because everything is same-origin through Next, the browser path needs no CORS. (FastAPI still sets `CORS_ORIGINS=http://localhost:3000` for direct `/docs`/debug calls.)

### 401-retry in `lib/api.ts`

```
request → 401 ?
  └─▶ POST /api/auth/refresh
        ├─ 200 → retry original request ONCE
        └─ 401 → redirect to /login
```

## Route protection (Next.js)

`src/middleware.ts` — matcher `['/feed', '/profile/:path*', '/post/:path*', '/login', '/register']`:
- Protected route + neither `access_token` nor `refresh_token` cookie present → redirect `/login`.
- `/login` or `/register` + cookies present → redirect `/feed`.
- Middleware checks cookie **presence only** — actual validation happens at the API (cheap, no JWT decode at the edge).

Server components needing data: read cookies via `cookies()` and call FastAPI directly with a Bearer header (`API_INTERNAL_URL`).

## FastAPI dependencies (`app/api/deps.py`)

- `get_current_user` — `HTTPBearer` security → `decode_token(.., "access")` → load user from DB → raise 401 (`WWW-Authenticate: Bearer`) on any failure → 403 if `not user.is_active`.
- `get_current_user_optional` — same, but returns `None` instead of raising — used by public GETs that personalize `my_reaction` / `shared_by_me`.

## Testing notes

pytest talks to FastAPI directly with Bearer headers (no cookies involved). The cookie layer is exercised manually in the browser (Phase 6 verification): devtools → Application → Cookies must show both tokens as httpOnly.
