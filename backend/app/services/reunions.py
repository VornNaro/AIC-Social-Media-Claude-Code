"""Reunion assembly: populate ReunionOut with host, going-count, and my RSVP."""
import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reunion import Reunion, Rsvp, RsvpStatus
from app.models.user import User
from app.schemas.post import AuthorMini
from app.schemas.reunion import ReunionOut


async def _going_counts(
    db: AsyncSession, reunion_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, int]:
    counts: dict[uuid.UUID, int] = {rid: 0 for rid in reunion_ids}
    if not reunion_ids:
        return counts
    for rid, count in (
        await db.execute(
            select(Rsvp.reunion_id, func.count())
            .where(Rsvp.reunion_id.in_(reunion_ids), Rsvp.status == RsvpStatus.GOING)
            .group_by(Rsvp.reunion_id)
        )
    ).all():
        counts[rid] = count
    return counts


async def _my_rsvps(
    db: AsyncSession, reunion_ids: Sequence[uuid.UUID], current_user: User | None
) -> dict[uuid.UUID, RsvpStatus]:
    mine: dict[uuid.UUID, RsvpStatus] = {}
    if current_user is None or not reunion_ids:
        return mine
    for rid, st in (
        await db.execute(
            select(Rsvp.reunion_id, Rsvp.status).where(
                Rsvp.reunion_id.in_(reunion_ids), Rsvp.user_id == current_user.id
            )
        )
    ).all():
        mine[rid] = st
    return mine


def _serialize(reunion: Reunion, going: int, my_rsvp: RsvpStatus | None) -> ReunionOut:
    return ReunionOut(
        id=reunion.id,
        school_id=reunion.school_id,
        title=reunion.title,
        class_year=reunion.class_year,
        starts_at=reunion.starts_at,
        ends_at=reunion.ends_at,
        venue=reunion.venue,
        address=reunion.address,
        city=reunion.city,
        cover_url=reunion.cover_url,
        description=reunion.description,
        amenities=reunion.amenities or [],
        host=AuthorMini.model_validate(reunion.host),
        going_count=going,
        my_rsvp=my_rsvp,
    )


async def assemble_reunions(
    db: AsyncSession, reunions: list[Reunion], current_user: User | None
) -> list[ReunionOut]:
    """Populate going-counts + my-RSVP for a list of (host-loaded) reunions."""
    ids = [r.id for r in reunions]
    going = await _going_counts(db, ids)
    mine = await _my_rsvps(db, ids, current_user)
    return [_serialize(r, going.get(r.id, 0), mine.get(r.id)) for r in reunions]


async def reunion_out(
    db: AsyncSession, reunion: Reunion, current_user: User | None
) -> ReunionOut:
    return (await assemble_reunions(db, [reunion], current_user))[0]


async def get_reunion_out(
    db: AsyncSession, reunion_id: uuid.UUID, current_user: User | None
) -> ReunionOut | None:
    reunion = await db.scalar(
        select(Reunion)
        .options(selectinload(Reunion.host))
        .where(Reunion.id == reunion_id)
        .execution_options(populate_existing=True)
    )
    if reunion is None:
        return None
    return await reunion_out(db, reunion, current_user)


async def list_reunions_for_school(
    db: AsyncSession, school_id: uuid.UUID, current_user: User | None
) -> list[ReunionOut]:
    reunions = list(
        (
            await db.scalars(
                select(Reunion)
                .options(selectinload(Reunion.host))
                .where(Reunion.school_id == school_id)
                .order_by(Reunion.starts_at.asc())
            )
        ).all()
    )
    return await assemble_reunions(db, reunions, current_user)
