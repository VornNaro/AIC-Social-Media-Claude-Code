from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

app = FastAPI(title="Social Hub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
