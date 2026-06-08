import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.post import Post
from app.models.share import Share
from app.models.user import User
from app.schemas.reaction import ShareState

router = APIRouter(tags=["shares"])


async def _share_state(
    db: AsyncSession, post_id: uuid.UUID, current_user: User
) -> ShareState:
    count = await db.scalar(
        select(func.count()).select_from(Share).where(Share.post_id == post_id)
    )
    mine = await db.scalar(
        select(Share.id).where(
            Share.post_id == post_id, Share.user_id == current_user.id
        )
    )
    return ShareState(share_count=count or 0, shared_by_me=mine is not None)


@router.post("/posts/{post_id}/shares", response_model=ShareState)
async def share_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareState:
    if await db.get(Post, post_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    # Idempotent insert: the UNIQUE(user_id, post_id) constraint makes a repeat a no-op.
    stmt = (
        pg_insert(Share)
        .values(post_id=post_id, user_id=current_user.id)
        .on_conflict_do_nothing(constraint="uq_shares_user_post")
    )
    await db.execute(stmt)
    await db.commit()
    return await _share_state(db, post_id, current_user)


@router.delete("/posts/{post_id}/shares", response_model=ShareState)
async def unshare_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareState:
    if await db.get(Post, post_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    existing = await db.scalar(
        select(Share).where(
            Share.post_id == post_id, Share.user_id == current_user.id
        )
    )
    if existing is not None:
        await db.delete(existing)
        await db.commit()
    return await _share_state(db, post_id, current_user)
