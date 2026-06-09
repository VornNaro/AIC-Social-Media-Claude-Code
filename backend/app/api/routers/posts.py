import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas.common import DEFAULT_LIMIT, CursorPage, clamp_limit
from app.schemas.post import AuthorMini, PostCreate, PostOut, PostUpdate
from app.services.feed import get_feed, get_post_out, serialize_post

router = APIRouter(tags=["posts"])

_EMPTY_META = {
    "reaction_counts": {},
    "my_reaction": None,
    "comment_count": 0,
    "share_count": 0,
    "shared_by_me": False,
}


async def _get_owned_post(post_id: uuid.UUID, user: User, db: AsyncSession) -> Post:
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the author of this post")
    return post


@router.get("/posts", response_model=CursorPage[PostOut])
async def feed(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=50),
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CursorPage[PostOut]:
    return await get_feed(db, clamp_limit(limit), cursor, current_user)


@router.post("/posts", status_code=status.HTTP_201_CREATED, response_model=PostOut)
async def create_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostOut:
    post = Post(
        author_id=current_user.id,
        content=body.content,
        image_url=body.image_url,
        tags=body.tags,
        note=body.note,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    post.author = current_user  # avoid a reload; we already have the author
    return serialize_post(post, dict(_EMPTY_META, reaction_counts={}))


@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> PostOut:
    post_out = await get_post_out(db, post_id, current_user)
    if post_out is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post_out


@router.patch("/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostOut:
    post = await _get_owned_post(post_id, current_user, db)
    data = body.model_dump(exclude_unset=True)
    if "content" in data:
        c = data["content"]
        post.content = c.strip() if c and c.strip() else None
    if "image_url" in data:
        post.image_url = data["image_url"] or None
    if "tags" in data:
        post.tags = data["tags"] or []
    if "note" in data:
        post.note = data["note"] or None
    if post.content is None and post.image_url is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A post must have content or an image.")
    await db.commit()
    post_out = await get_post_out(db, post_id, current_user)
    assert post_out is not None
    return post_out


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    post = await _get_owned_post(post_id, current_user, db)
    await db.delete(post)
    await db.commit()
