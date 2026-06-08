import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.common import DEFAULT_LIMIT, CursorPage, clamp_limit, decode_cursor, encode_cursor

router = APIRouter(tags=["comments"])


async def _ensure_post_exists(post_id: uuid.UUID, db: AsyncSession) -> None:
    if await db.get(Post, post_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


@router.get("/posts/{post_id}/comments", response_model=CursorPage[CommentOut])
async def list_comments(
    post_id: uuid.UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=50),
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_current_user_optional),
) -> CursorPage[CommentOut]:
    await _ensure_post_exists(post_id, db)
    limit = clamp_limit(limit)
    stmt = (
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .limit(limit + 1)
    )
    if cursor:
        t, cid = decode_cursor(cursor)
        stmt = stmt.where(tuple_(Comment.created_at, Comment.id) > tuple_(t, cid))

    comments = list((await db.scalars(stmt)).all())
    has_more = len(comments) > limit
    comments = comments[:limit]
    items = [CommentOut.model_validate(_to_out(c)) for c in comments]
    next_cursor = (
        encode_cursor(comments[-1].created_at, comments[-1].id) if has_more and comments else None
    )
    return CursorPage[CommentOut](items=items, next_cursor=next_cursor, has_more=has_more)


def _to_out(c: Comment) -> dict:
    return {
        "id": c.id,
        "post_id": c.post_id,
        "author": c.author,
        "content": c.content,
        "created_at": c.created_at,
    }


@router.post(
    "/posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentOut,
)
async def create_comment(
    post_id: uuid.UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    await _ensure_post_exists(post_id, db)
    comment = Comment(post_id=post_id, author_id=current_user.id, content=body.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    comment.author = current_user
    return CommentOut.model_validate(_to_out(comment))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the author of this comment")
    await db.delete(comment)
    await db.commit()
