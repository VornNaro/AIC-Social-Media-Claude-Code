import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.reunion import Reunion, Rsvp, RsvpStatus
from app.models.user import User
from app.schemas.reunion import AttendeeOut, ReunionOut, RsvpIn
from app.services.reunions import (
    _going_counts,
    _my_rsvps,
    _serialize,
    get_reunion_out,
)

router = APIRouter(tags=["reunions"])


@router.get("/reunions", response_model=list[ReunionOut])
async def list_reunions(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ReunionOut]:
    """Upcoming reunions across all schools, soonest first (feed right rail)."""
    reunions = list(
        (
            await db.scalars(
                select(Reunion)
                .options(selectinload(Reunion.host))
                .where(Reunion.starts_at >= datetime.now(timezone.utc))
                .order_by(Reunion.starts_at.asc())
                .limit(limit)
            )
        ).all()
    )
    ids = [r.id for r in reunions]
    going = await _going_counts(db, ids)
    mine = await _my_rsvps(db, ids, current_user)
    return [_serialize(r, going.get(r.id, 0), mine.get(r.id)) for r in reunions]


@router.get("/reunions/{reunion_id}", response_model=ReunionOut)
async def get_reunion(
    reunion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ReunionOut:
    out = await get_reunion_out(db, reunion_id, current_user)
    if out is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunion not found")
    return out


@router.put("/reunions/{reunion_id}/rsvp", response_model=ReunionOut)
async def set_rsvp(
    reunion_id: uuid.UUID,
    body: RsvpIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReunionOut:
    reunion = await db.get(Reunion, reunion_id)
    if reunion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunion not found")
    existing = await db.scalar(
        select(Rsvp).where(
            Rsvp.reunion_id == reunion_id, Rsvp.user_id == current_user.id
        )
    )
    if existing is None:
        db.add(Rsvp(reunion_id=reunion_id, user_id=current_user.id, status=body.status))
    else:
        existing.status = body.status
    await db.commit()
    out = await get_reunion_out(db, reunion_id, current_user)
    assert out is not None
    return out


@router.delete("/reunions/{reunion_id}/rsvp", response_model=ReunionOut)
async def clear_rsvp(
    reunion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReunionOut:
    existing = await db.scalar(
        select(Rsvp).where(
            Rsvp.reunion_id == reunion_id, Rsvp.user_id == current_user.id
        )
    )
    if existing is not None:
        await db.delete(existing)
        await db.commit()
    out = await get_reunion_out(db, reunion_id, current_user)
    if out is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunion not found")
    return out


@router.get("/reunions/{reunion_id}/attendees", response_model=list[AttendeeOut])
async def list_attendees(
    reunion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttendeeOut]:
    rows = (
        await db.execute(
            select(User, Rsvp.status)
            .join(Rsvp, Rsvp.user_id == User.id)
            .where(Rsvp.reunion_id == reunion_id, Rsvp.status != RsvpStatus.DECLINED)
            .order_by(Rsvp.status, User.display_name)
        )
    ).all()
    return [
        AttendeeOut(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            graduation_year=u.graduation_year,
            city=u.city,
            status=st,
        )
        for (u, st) in rows
    ]
