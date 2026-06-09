import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.connection import Connection, ConnectionStatus
from app.models.school import SchoolMembership
from app.models.user import User
from app.schemas.connection import ClassmateOut, ConnectionOut, ConnectionRequest

router = APIRouter(tags=["connections"])


async def _accepted_neighbor_ids(db: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    rows = (
        await db.execute(
            select(Connection.requester_id, Connection.addressee_id).where(
                Connection.status == ConnectionStatus.ACCEPTED,
                or_(
                    Connection.requester_id == user_id,
                    Connection.addressee_id == user_id,
                ),
            )
        )
    ).all()
    out: set[uuid.UUID] = set()
    for req, addr in rows:
        out.add(addr if req == user_id else req)
    return out


def _classmate(u: User, state: str, mutual: int = 0) -> ClassmateOut:
    return ClassmateOut.from_user(u, connection_state=state, mutual_count=mutual)


@router.get("/connections", response_model=list[ClassmateOut])
async def my_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ClassmateOut]:
    ids = await _accepted_neighbor_ids(db, current_user.id)
    if not ids:
        return []
    users = (await db.scalars(select(User).where(User.id.in_(ids)))).all()
    return [_classmate(u, "connected") for u in users]


@router.get("/connections/requests", response_model=list[ClassmateOut])
async def incoming_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ClassmateOut]:
    rows = (
        await db.execute(
            select(User)
            .join(Connection, Connection.requester_id == User.id)
            .where(
                Connection.addressee_id == current_user.id,
                Connection.status == ConnectionStatus.PENDING,
            )
        )
    ).scalars().all()
    return [_classmate(u, "pending_incoming") for u in rows]


@router.get("/connections/suggestions", response_model=list[ClassmateOut])
async def suggestions(
    limit: int = Query(default=6, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ClassmateOut]:
    """Classmates from my school I'm not connected to yet, with mutual counts."""
    my_friends = await _accepted_neighbor_ids(db, current_user.id)

    # any existing connection (pending or accepted) excludes the candidate
    related = (
        await db.execute(
            select(Connection.requester_id, Connection.addressee_id).where(
                or_(
                    Connection.requester_id == current_user.id,
                    Connection.addressee_id == current_user.id,
                )
            )
        )
    ).all()
    excluded = {current_user.id}
    for req, addr in related:
        excluded.add(addr if req == current_user.id else req)

    stmt = select(User).where(User.id.notin_(excluded))
    if current_user.school_id is not None:
        stmt = stmt.join(
            SchoolMembership, SchoolMembership.user_id == User.id
        ).where(SchoolMembership.school_id == current_user.school_id)
    stmt = stmt.limit(limit * 3)
    candidates = list((await db.scalars(stmt)).all())

    # mutual counts: candidates' accepted neighbors ∩ my friends
    cand_ids = [c.id for c in candidates]
    mutual: dict[uuid.UUID, int] = {cid: 0 for cid in cand_ids}
    if cand_ids and my_friends:
        rows = (
            await db.execute(
                select(Connection.requester_id, Connection.addressee_id).where(
                    Connection.status == ConnectionStatus.ACCEPTED,
                    or_(
                        Connection.requester_id.in_(cand_ids),
                        Connection.addressee_id.in_(cand_ids),
                    ),
                )
            )
        ).all()
        for req, addr in rows:
            for cid, other in ((req, addr), (addr, req)):
                if cid in mutual and other in my_friends:
                    mutual[cid] += 1

    candidates.sort(key=lambda c: mutual[c.id], reverse=True)
    return [_classmate(c, "none", mutual[c.id]) for c in candidates[:limit]]


@router.post("/connections", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
async def request_connection(
    body: ConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConnectionOut:
    target_id = body.user_id
    if target_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't connect with yourself")
    target = await db.get(User, target_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = await db.scalar(
        select(Connection).where(
            or_(
                (Connection.requester_id == current_user.id)
                & (Connection.addressee_id == target_id),
                (Connection.requester_id == target_id)
                & (Connection.addressee_id == current_user.id),
            )
        )
    )
    if existing is not None:
        if (
            existing.status == ConnectionStatus.PENDING
            and existing.addressee_id == current_user.id
        ):
            # They already requested me — accept it.
            existing.status = ConnectionStatus.ACCEPTED
        elif existing.status == ConnectionStatus.DECLINED:
            # A prior decline shouldn't permanently block reconnecting: reopen the
            # request in the current direction.
            existing.requester_id = current_user.id
            existing.addressee_id = target_id
            existing.status = ConnectionStatus.PENDING
        else:
            # Already pending (outgoing) or accepted — idempotent.
            return ConnectionOut.model_validate(existing)
        await db.commit()
        await db.refresh(existing)
        return ConnectionOut.model_validate(existing)

    conn = Connection(
        requester_id=current_user.id,
        addressee_id=target_id,
        status=ConnectionStatus.PENDING,
    )
    db.add(conn)
    try:
        await db.commit()
    except IntegrityError:
        # Raced a concurrent request on the same pair — return the winning row.
        await db.rollback()
        conn = await db.scalar(
            select(Connection).where(
                or_(
                    (Connection.requester_id == current_user.id)
                    & (Connection.addressee_id == target_id),
                    (Connection.requester_id == target_id)
                    & (Connection.addressee_id == current_user.id),
                )
            )
        )
        if conn is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Could not create connection") from None
        return ConnectionOut.model_validate(conn)
    await db.refresh(conn)
    return ConnectionOut.model_validate(conn)


@router.post("/connections/{user_id}/accept", response_model=ConnectionOut)
async def accept_connection(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConnectionOut:
    conn = await db.scalar(
        select(Connection).where(
            Connection.requester_id == user_id,
            Connection.addressee_id == current_user.id,
            Connection.status == ConnectionStatus.PENDING,
        )
    )
    if conn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No pending request from this user")
    conn.status = ConnectionStatus.ACCEPTED
    await db.commit()
    await db.refresh(conn)
    return ConnectionOut.model_validate(conn)


@router.delete("/connections/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    conn = await db.scalar(
        select(Connection).where(
            or_(
                (Connection.requester_id == current_user.id)
                & (Connection.addressee_id == user_id),
                (Connection.requester_id == user_id)
                & (Connection.addressee_id == current_user.id),
            )
        )
    )
    if conn is not None:
        await db.delete(conn)
        await db.commit()
