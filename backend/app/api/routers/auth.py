import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    CredentialsError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.school import SchoolMembership
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services.schools import find_or_create_school
from app.services.users import build_user_out

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    """Create an access+refresh pair and persist the refresh jti."""
    access = create_access_token(user.id)
    refresh, jti, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at))
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    email = body.email.lower()
    existing = await db.scalar(
        select(User).where(or_(User.username == body.username, User.email == email))
    )
    if existing is not None:
        detail = (
            "Username already taken"
            if existing.username == body.username
            else "Email already registered"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    user = User(
        username=body.username,
        email=email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name or body.username,
        graduation_year=body.graduation_year,
        avatar_url=body.avatar_url,
    )
    db.add(user)
    await db.flush()  # assign user.id

    # Find-or-create the school by name and join it.
    if body.school_name and body.school_name.strip():
        school = await find_or_create_school(db, body.school_name.strip())
        user.school_id = school.id
        db.add(SchoolMembership(school_id=school.id, user_id=user.id))

    pair = await _issue_token_pair(db, user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(**pair.model_dump(), user=await build_user_out(db, user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    ident = body.username_or_email.strip().lower()
    user = await db.scalar(
        select(User).where(or_(User.username == ident, User.email == ident))
    )
    # Same generic error whether the user is missing or the password is wrong.
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    pair = await _issue_token_pair(db, user)
    await db.commit()
    return AuthResponse(**pair.model_dump(), user=await build_user_out(db, user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token, "refresh")
        jti = uuid.UUID(payload["jti"])
        user_id = uuid.UUID(payload["sub"])
    except (CredentialsError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    token_row = await db.get(RefreshToken, jti)

    # Unknown or already-revoked jti => reuse/theft: revoke ALL of the user's tokens.
    if token_row is None or token_row.revoked:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Rotate: revoke the presented token, issue a fresh pair.
    token_row.revoked = True
    pair = await _issue_token_pair(db, user)
    await db.commit()
    return pair


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)) -> None:
    try:
        payload = decode_token(body.refresh_token, "refresh")
        jti = uuid.UUID(payload["jti"])
    except (CredentialsError, KeyError, ValueError):
        return  # idempotent — nothing to revoke

    token_row = await db.get(RefreshToken, jti)
    if token_row is not None and not token_row.revoked:
        token_row.revoked = True
        await db.commit()


@router.get("/me", response_model=UserOut)
async def me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    return await build_user_out(db, current_user)
