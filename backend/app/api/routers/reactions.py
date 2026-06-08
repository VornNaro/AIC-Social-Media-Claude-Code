import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.post import Post
from app.models.reaction import Reaction
from app.models.user import User
from app.schemas.reaction import ReactionRequest, ReactionState

router = APIRouter(tags=["reactions"])


async def _ensure_post_exists(post_id: uuid.UUID, db: AsyncSession) -> None:
    if await db.get(Post, post_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


async def _reaction_state(
    db: AsyncSession, post_id: uuid.UUID, current_user: User | None
) -> ReactionState:
    counts: dict[str, int] = {}
    for rtype, count in (
        await db.execute(
            select(Reaction.type, func.count())
            .where(Reaction.post_id == post_id)
            .group_by(Reaction.type)
        )
    ).all():
        counts[rtype.value] = count

    my_reaction = None
    if current_user is not None:
        my_reaction = await db.scalar(
            select(Reaction.type).where(
                Reaction.post_id == post_id, Reaction.user_id == current_user.id
            )
        )
    return ReactionState(my_reaction=my_reaction, reaction_counts=counts)


@router.put("/posts/{post_id}/reactions", response_model=ReactionState)
async def set_reaction(
    post_id: uuid.UUID,
    body: ReactionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReactionState:
    await _ensure_post_exists(post_id, db)
    current_type = await db.scalar(
        select(Reaction.type).where(
            Reaction.post_id == post_id, Reaction.user_id == current_user.id
        )
    )
    if current_type == body.type:
        # same type again => toggle off
        await db.execute(
            delete(Reaction).where(
                Reaction.post_id == post_id, Reaction.user_id == current_user.id
            )
        )
    else:
        # insert or switch — atomic via the unique constraint (no race -> no 500)
        await db.execute(
            pg_insert(Reaction)
            .values(post_id=post_id, user_id=current_user.id, type=body.type)
            .on_conflict_do_update(
                constraint="uq_reactions_user_post", set_={"type": body.type}
            )
        )
    await db.commit()
    return await _reaction_state(db, post_id, current_user)


@router.delete("/posts/{post_id}/reactions", response_model=ReactionState)
async def remove_reaction(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReactionState:
    await _ensure_post_exists(post_id, db)
    existing = await db.scalar(
        select(Reaction).where(
            Reaction.post_id == post_id, Reaction.user_id == current_user.id
        )
    )
    if existing is not None:
        await db.delete(existing)
        await db.commit()
    return await _reaction_state(db, post_id, current_user)


@router.get("/posts/{post_id}/reactions", response_model=ReactionState)
async def get_reactions(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ReactionState:
    await _ensure_post_exists(post_id, db)
    return await _reaction_state(db, post_id, current_user)
