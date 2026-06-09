"""Feed assembly: turn posts (and reposts) into fully-populated PostOut objects.

All count/reaction lookups are done in a few grouped queries keyed by post id,
so building a page of N posts costs a constant number of queries (no N+1).
"""
import uuid
from collections.abc import Sequence

from sqlalchemy import cast, func, null, select, tuple_, union_all
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment
from app.models.post import Post
from app.models.reaction import Reaction
from app.models.share import Share
from app.models.user import User
from app.schemas.common import CursorPage, decode_cursor, encode_cursor
from app.schemas.post import AuthorMini, PostOut, SharedBy


async def _aggregate_meta(
    db: AsyncSession, post_ids: Sequence[uuid.UUID], current_user: User | None
) -> dict[uuid.UUID, dict]:
    """Return per-post counts + the current user's reaction/share state."""
    meta: dict[uuid.UUID, dict] = {
        pid: {
            "reaction_counts": {},
            "my_reaction": None,
            "comment_count": 0,
            "share_count": 0,
            "shared_by_me": False,
        }
        for pid in post_ids
    }
    if not post_ids:
        return meta

    # Reaction counts grouped by post + type.
    for pid, rtype, count in (
        await db.execute(
            select(Reaction.post_id, Reaction.type, func.count())
            .where(Reaction.post_id.in_(post_ids))
            .group_by(Reaction.post_id, Reaction.type)
        )
    ).all():
        meta[pid]["reaction_counts"][rtype.value] = count

    # Comment counts.
    for pid, count in (
        await db.execute(
            select(Comment.post_id, func.count())
            .where(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
        )
    ).all():
        meta[pid]["comment_count"] = count

    # Share counts.
    for pid, count in (
        await db.execute(
            select(Share.post_id, func.count())
            .where(Share.post_id.in_(post_ids))
            .group_by(Share.post_id)
        )
    ).all():
        meta[pid]["share_count"] = count

    # Current user's own reaction + shares.
    if current_user is not None:
        for pid, rtype in (
            await db.execute(
                select(Reaction.post_id, Reaction.type).where(
                    Reaction.post_id.in_(post_ids), Reaction.user_id == current_user.id
                )
            )
        ).all():
            meta[pid]["my_reaction"] = rtype.value

        for (pid,) in (
            await db.execute(
                select(Share.post_id).where(
                    Share.post_id.in_(post_ids), Share.user_id == current_user.id
                )
            )
        ).all():
            meta[pid]["shared_by_me"] = True

    return meta


def serialize_post(post: Post, meta: dict, shared_by: SharedBy | None = None) -> PostOut:
    return PostOut(
        id=post.id,
        author=AuthorMini.model_validate(post.author),
        content=post.content,
        image_url=post.image_url,
        tags=post.tags or [],
        note=post.note,
        created_at=post.created_at,
        updated_at=post.updated_at,
        reaction_counts=meta["reaction_counts"],
        my_reaction=meta["my_reaction"],
        comment_count=meta["comment_count"],
        share_count=meta["share_count"],
        shared_by_me=meta["shared_by_me"],
        shared_by=shared_by,
    )


async def get_post_out(
    db: AsyncSession, post_id: uuid.UUID, current_user: User | None
) -> PostOut | None:
    post = await db.scalar(
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.id == post_id)
        .execution_options(populate_existing=True)
    )
    if post is None:
        return None
    meta = await _aggregate_meta(db, [post_id], current_user)
    return serialize_post(post, meta[post_id])


async def _paginate_posts(
    db: AsyncSession,
    where: object,
    limit: int,
    cursor: str | None,
    current_user: User | None,
) -> CursorPage[PostOut]:
    """Cursor-paginate authored posts (newest first) matching `where`."""
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(where)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .limit(limit + 1)
        .execution_options(populate_existing=True)
    )
    if cursor:
        t, cid = decode_cursor(cursor)
        stmt = stmt.where(tuple_(Post.created_at, Post.id) < tuple_(t, cid))

    posts = list((await db.scalars(stmt)).all())
    has_more = len(posts) > limit
    posts = posts[:limit]

    meta = await _aggregate_meta(db, [p.id for p in posts], current_user)
    items = [serialize_post(p, meta[p.id]) for p in posts]
    next_cursor = (
        encode_cursor(posts[-1].created_at, posts[-1].id) if has_more and posts else None
    )
    return CursorPage[PostOut](items=items, next_cursor=next_cursor, has_more=has_more)


async def list_authored_posts(
    db: AsyncSession,
    author_id: uuid.UUID,
    limit: int,
    cursor: str | None,
    current_user: User | None,
) -> CursorPage[PostOut]:
    """Posts authored by a single user (no reposts), newest first."""
    return await _paginate_posts(db, Post.author_id == author_id, limit, cursor, current_user)


async def list_school_posts(
    db: AsyncSession,
    school_id: uuid.UUID,
    limit: int,
    cursor: str | None,
    current_user: User | None,
) -> CursorPage[PostOut]:
    """Posts authored by members of a school (the group "Memories" feed)."""
    from app.models.school import SchoolMembership

    member_ids = select(SchoolMembership.user_id).where(
        SchoolMembership.school_id == school_id
    )
    return await _paginate_posts(
        db, Post.author_id.in_(member_ids), limit, cursor, current_user
    )


async def get_feed(
    db: AsyncSession, limit: int, cursor: str | None, current_user: User | None
) -> CursorPage[PostOut]:
    """Global feed: original posts UNION reposts, ordered by event time desc."""
    post_events = select(
        Post.id.label("post_id"),
        Post.created_at.label("event_time"),
        Post.id.label("event_id"),
        cast(null(), PGUUID(as_uuid=True)).label("sharer_id"),
    )
    share_events = select(
        Share.post_id.label("post_id"),
        Share.created_at.label("event_time"),
        Share.id.label("event_id"),
        Share.user_id.label("sharer_id"),
    )
    feed = union_all(post_events, share_events).subquery("feed")

    stmt = (
        select(feed)
        .order_by(feed.c.event_time.desc(), feed.c.event_id.desc())
        .limit(limit + 1)
    )
    if cursor:
        t, cid = decode_cursor(cursor)
        stmt = stmt.where(tuple_(feed.c.event_time, feed.c.event_id) < tuple_(t, cid))

    rows = (await db.execute(stmt)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    post_ids = list({r.post_id for r in rows})
    sharer_ids = list({r.sharer_id for r in rows if r.sharer_id is not None})

    posts = (
        await db.scalars(
            select(Post)
            .options(selectinload(Post.author))
            .where(Post.id.in_(post_ids))
            .execution_options(populate_existing=True)
        )
    ).all()
    post_map = {p.id: p for p in posts}
    sharers = (
        (await db.scalars(select(User).where(User.id.in_(sharer_ids)))).all()
        if sharer_ids
        else []
    )
    sharer_map = {u.id: u for u in sharers}

    meta = await _aggregate_meta(db, post_ids, current_user)

    items: list[PostOut] = []
    for r in rows:
        post = post_map.get(r.post_id)
        if post is None:
            continue
        shared_by = None
        if r.sharer_id is not None and r.sharer_id in sharer_map:
            sharer = sharer_map[r.sharer_id]
            shared_by = SharedBy(
                username=sharer.username,
                display_name=sharer.display_name,
                shared_at=r.event_time,
            )
        items.append(serialize_post(post, meta[r.post_id], shared_by))

    next_cursor = (
        encode_cursor(rows[-1].event_time, rows[-1].event_id) if has_more and rows else None
    )
    return CursorPage[PostOut](items=items, next_cursor=next_cursor, has_more=has_more)
