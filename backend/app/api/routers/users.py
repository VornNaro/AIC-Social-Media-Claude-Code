from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import DEFAULT_LIMIT, CursorPage, clamp_limit
from app.schemas.post import PostOut
from app.schemas.user import UserOut, UserProfile, UserUpdate
from app.services.feed import list_authored_posts
from app.services.users import build_user_out, build_user_profile

router = APIRouter(tags=["users"])


@router.patch("/users/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return await build_user_out(db, current_user)


@router.get("/users/{username}", response_model=UserProfile)
async def get_profile(
    username: str, db: AsyncSession = Depends(get_db)
) -> UserProfile:
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return await build_user_profile(db, user)


@router.get("/users/{username}/posts", response_model=CursorPage[PostOut])
async def get_user_posts(
    username: str,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=50),
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CursorPage[PostOut]:
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return await list_authored_posts(db, user.id, clamp_limit(limit), cursor, current_user)
