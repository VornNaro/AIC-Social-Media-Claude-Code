import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.connection import Connection, ConnectionStatus
from app.models.reunion import Reunion, Rsvp, RsvpStatus
from app.models.school import School, SchoolMembership
from app.models.user import User
from app.schemas.common import DEFAULT_LIMIT, CursorPage, clamp_limit
from app.schemas.connection import ClassmateOut
from app.schemas.post import PostOut
from app.schemas.reunion import ReunionCreate, ReunionOut
from app.schemas.school import SchoolCreate, SchoolOut
from app.services.feed import list_school_posts
from app.services.schools import find_or_create_school

router = APIRouter(tags=["schools"])


async def _school_out(
    db: AsyncSession, school: School, current_user: User | None
) -> SchoolOut:
    member_count = await db.scalar(
        select(func.count()).select_from(SchoolMembership).where(
            SchoolMembership.school_id == school.id
        )
    )
    is_member = False
    if current_user is not None:
        is_member = (
            await db.scalar(
                select(SchoolMembership.id).where(
                    SchoolMembership.school_id == school.id,
                    SchoolMembership.user_id == current_user.id,
                )
            )
        ) is not None
    return SchoolOut(
        id=school.id,
        slug=school.slug,
        name=school.name,
        short_name=school.short_name,
        location=school.location,
        founded=school.founded,
        cover_url=school.cover_url,
        motto=school.motto,
        member_count=member_count or 0,
        is_member=is_member,
        created_at=school.created_at,
    )


async def _get_school(db: AsyncSession, slug: str) -> School:
    school = await db.scalar(select(School).where(School.slug == slug.lower()))
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return school


@router.post("/schools", response_model=SchoolOut, status_code=status.HTTP_201_CREATED)
async def create_school(
    body: SchoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchoolOut:
    """Find-or-create a school by name (idempotent on its slug)."""
    school = await find_or_create_school(
        db,
        body.name,
        short_name=body.short_name,
        location=body.location,
        founded=body.founded,
        cover_url=body.cover_url,
        motto=body.motto,
    )
    await db.commit()
    await db.refresh(school)
    return await _school_out(db, school, current_user)


@router.get("/schools/{slug}", response_model=SchoolOut)
async def get_school(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> SchoolOut:
    school = await _get_school(db, slug)
    return await _school_out(db, school, current_user)


@router.post("/schools/{slug}/join", response_model=SchoolOut)
async def join_school(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchoolOut:
    school = await _get_school(db, slug)
    already = await db.scalar(
        select(SchoolMembership.id).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == current_user.id,
        )
    )
    if already is None:
        db.add(SchoolMembership(school_id=school.id, user_id=current_user.id))
        # adopt this school as the user's primary if they have none
        if current_user.school_id is None:
            current_user.school_id = school.id
        await db.commit()
    return await _school_out(db, school, current_user)


@router.delete("/schools/{slug}/join", response_model=SchoolOut)
async def leave_school(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchoolOut:
    school = await _get_school(db, slug)
    membership = await db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == current_user.id,
        )
    )
    if membership is not None:
        await db.delete(membership)
        if current_user.school_id == school.id:
            current_user.school_id = None
        await db.commit()
    return await _school_out(db, school, current_user)


async def _connection_states(
    db: AsyncSession, me: User, others: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """Map each other-user id → my connection state with them."""
    states: dict[uuid.UUID, str] = {}
    if not others:
        return states
    rows = (
        await db.execute(
            select(Connection).where(
                or_(
                    Connection.requester_id == me.id,
                    Connection.addressee_id == me.id,
                ),
                or_(
                    Connection.requester_id.in_(others),
                    Connection.addressee_id.in_(others),
                ),
            )
        )
    ).scalars().all()
    for c in rows:
        other = c.addressee_id if c.requester_id == me.id else c.requester_id
        if c.status == ConnectionStatus.ACCEPTED:
            states[other] = "connected"
        elif c.status == ConnectionStatus.PENDING:
            states[other] = (
                "pending_outgoing" if c.requester_id == me.id else "pending_incoming"
            )
    return states


@router.get("/schools/{slug}/members", response_model=list[ClassmateOut])
async def list_members(
    slug: str,
    year: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=60, ge=1, le=120),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ClassmateOut]:
    school = await _get_school(db, slug)
    stmt = (
        select(User)
        .join(SchoolMembership, SchoolMembership.user_id == User.id)
        .where(SchoolMembership.school_id == school.id)
    )
    if current_user is not None:
        stmt = stmt.where(User.id != current_user.id)
    if year is not None:
        stmt = stmt.where(User.graduation_year == year)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(User.display_name).like(like), func.lower(User.city).like(like))
        )
    stmt = stmt.order_by(User.display_name).limit(limit)
    users = list((await db.scalars(stmt)).all())

    states: dict[uuid.UUID, str] = {}
    if current_user is not None:
        states = await _connection_states(db, current_user, [u.id for u in users])

    return [
        ClassmateOut(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            graduation_year=u.graduation_year,
            city=u.city,
            role=u.role,
            connection_state=states.get(u.id, "none"),
        )
        for u in users
    ]


@router.get("/schools/{slug}/posts", response_model=CursorPage[PostOut])
async def school_posts(
    slug: str,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=50),
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CursorPage[PostOut]:
    school = await _get_school(db, slug)
    return await list_school_posts(db, school.id, clamp_limit(limit), cursor, current_user)


@router.get("/schools/{slug}/reunions", response_model=list[ReunionOut])
async def school_reunions(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ReunionOut]:
    from app.services.reunions import list_reunions_for_school

    school = await _get_school(db, slug)
    return await list_reunions_for_school(db, school.id, current_user)


@router.post(
    "/schools/{slug}/reunions",
    response_model=ReunionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_reunion(
    slug: str,
    body: ReunionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReunionOut:
    from app.services.reunions import reunion_out

    school = await _get_school(db, slug)
    reunion = Reunion(
        school_id=school.id,
        host_id=current_user.id,
        title=body.title,
        class_year=body.class_year,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        venue=body.venue,
        address=body.address,
        city=body.city,
        cover_url=body.cover_url,
        description=body.description,
        amenities=body.amenities,
    )
    # host auto-RSVPs as going
    db.add(reunion)
    await db.flush()
    db.add(Rsvp(reunion_id=reunion.id, user_id=current_user.id, status=RsvpStatus.GOING))
    await db.commit()
    reunion.host = current_user
    return await reunion_out(db, reunion, current_user)
