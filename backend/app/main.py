from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routers import auth, comments, posts, reactions, shares, users
from app.core.config import settings
from app.core.database import engine

app = FastAPI(title="Social Hub API", version="0.1.0")

# FastAPI is a pure Bearer API — tokens travel in the Authorization header, not
# cookies (the Next.js proxy owns cookies, server-side, where CORS doesn't apply).
# So we do NOT enable credentialed CORS, and we refuse a wildcard origin to avoid
# ever reflecting "*" back to browsers.
_cors_origins = settings.cors_origins_list
if "*" in _cors_origins:
    raise RuntimeError("CORS_ORIGINS must list explicit origins, not '*'.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(reactions.router, prefix="/api/v1")
app.include_router(shares.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness check — returns ok if the app is up."""
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
async def health_db() -> dict[str, str]:
    """Readiness check — verifies the database connection."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


# Routers are included here in later phases (auth, users, posts, ...).
