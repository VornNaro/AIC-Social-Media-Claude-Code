import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


class CredentialsError(Exception):
    """Raised when a token is missing, malformed, expired, or the wrong type."""


# --- Passwords (bcrypt) ---------------------------------------------------

def hash_password(plain: str) -> str:
    # bcrypt operates on bytes and caps input at 72 bytes.
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# --- JWT ------------------------------------------------------------------

def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, uuid.UUID, datetime]:
    """Returns (token, jti, expires_at). The jti is tracked in refresh_tokens."""
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4()
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(jti),
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str, expected_type: str) -> dict:
    """Decode and validate a token. Raises CredentialsError on any problem."""
    key = settings.JWT_SECRET_KEY if expected_type == "access" else settings.JWT_REFRESH_SECRET_KEY
    try:
        payload = jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise CredentialsError("Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise CredentialsError("Wrong token type")
    return payload
