import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CredentialsError, decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _load_user_from_token(token: str, db: AsyncSession) -> User | None:
    try:
        payload = decode_token(token, "access")
        user_id = uuid.UUID(payload["sub"])
    except (CredentialsError, KeyError, ValueError):
        return None
    return await db.get(User, user_id)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a valid access token; returns the active user or raises 401/403."""
    if credentials is None:
        raise _UNAUTHORIZED
    user = await _load_user_from_token(credentials.credentials, db)
    if user is None:
        raise _UNAUTHORIZED
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the user if a valid token is present, else None (for public endpoints)."""
    if credentials is None:
        return None
    user = await _load_user_from_token(credentials.credentials, db)
    if user is None or not user.is_active:
        return None
    return user
