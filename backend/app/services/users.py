"""User serialization helpers that eager-load the user's school relationship."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connection import Connection, ConnectionStatus
from app.models.post import Post
from app.models.school import School
from app.models.user import User
from app.schemas.user import SchoolMini, UserOut, UserProfile


async def _school_mini(db: AsyncSession, school_id: uuid.UUID | None) -> SchoolMini | None:
    if school_id is None:
        return None
    school = await db.get(School, school_id)
    return SchoolMini.model_validate(school) if school is not None else None


async def build_user_out(db: AsyncSession, user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.school = await _school_mini(db, user.school_id)
    return out


async def build_user_profile(db: AsyncSession, user: User) -> UserProfile:
    post_count = await db.scalar(
        select(func.count()).select_from(Post).where(Post.author_id == user.id)
    )
    connection_count = await db.scalar(
        select(func.count())
        .select_from(Connection)
        .where(
            Connection.status == ConnectionStatus.ACCEPTED,
            or_(
                Connection.requester_id == user.id,
                Connection.addressee_id == user.id,
            ),
        )
    )
    return UserProfile(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        cover_url=user.cover_url,
        graduation_year=user.graduation_year,
        city=user.city,
        role=user.role,
        interests=user.interests or [],
        school=await _school_mini(db, user.school_id),
        created_at=user.created_at,
        post_count=post_count or 0,
        connection_count=connection_count or 0,
    )
