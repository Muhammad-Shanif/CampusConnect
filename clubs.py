"""Club, membership and officer endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError
from app.db import acquire, call_proc, execute, fetch_many, fetch_one
from app.db import queries as Q
from app.models import (
    AssignOfficerIn, ClubCreate, ClubOut, ClubUpdate, EventOut, JoinClubIn, MemberOut,
    MembershipStatusIn, Message, OfficerOut, Page,
)
from app.routers.deps import get_db_pool, like

router = APIRouter(prefix="/clubs", tags=["clubs"])
memberships_router = APIRouter(prefix="/memberships", tags=["clubs"])


async def _club_or_404(conn: aiomysql.Connection, club_id: int) -> dict:
    row = await fetch_one(conn, Q.CLUB_BY_ID, (club_id,))
    if not row:
        raise NotFoundError(f"Club {club_id} not found")
    return row


@router.get("", response_model=Page[ClubOut])
async def list_clubs(
    q: str | None = None,
    category: str | None = None,
    status: str | None = None,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[ClubOut]:
    pattern = like(q)
    async with acquire(pool) as conn:
        rows = await fetch_many(
            conn, Q.CLUBS_LIST, (pattern, pattern, category, category, status, status)
        )
    return Page(total=len(rows), items=[ClubOut(**r) for r in rows])


@router.post("", response_model=ClubOut, status_code=201)
async def create_club(payload: ClubCreate, pool: aiomysql.Pool = Depends(get_db_pool)) -> ClubOut:
    async with acquire(pool) as conn:
        new_id, _ = await execute(
            conn, Q.CLUB_INSERT,
            (payload.club_name, payload.description, payload.category,
             payload.date_founded, payload.status),
        )
        row = await _club_or_404(conn, new_id)
    return ClubOut(**row)


@router.get("/{club_id}", response_model=ClubOut)
async def get_club(club_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> ClubOut:
    async with acquire(pool) as conn:
        row = await _club_or_404(conn, club_id)
    return ClubOut(**row)


@router.put("/{club_id}", response_model=ClubOut)
async def update_club(
    club_id: int, payload: ClubUpdate, pool: aiomysql.Pool = Depends(get_db_pool)
) -> ClubOut:
    async with acquire(pool) as conn:
        current = await fetch_one(conn, Q.CLUB_BASE_BY_ID, (club_id,))
        if not current:
            raise NotFoundError(f"Club {club_id} not found")
        current.update(payload.model_dump(exclude_unset=True))
        await execute(
            conn, Q.CLUB_UPDATE,
            (current["club_name"], current["description"], current["category"],
             current["date_founded"], current["status"], club_id),
        )
        row = await _club_or_404(conn, club_id)
    return ClubOut(**row)


@router.delete("/{club_id}", response_model=Message)
async def delete_club(club_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Message:
    """Fails with 409 when the club still has events (FK RESTRICT)."""
    async with acquire(pool) as conn:
        _, count = await execute(conn, Q.CLUB_DELETE, (club_id,))
    if count == 0:
        raise NotFoundError(f"Club {club_id} not found")
    return Message(detail="Club deleted")


@router.get("/{club_id}/members", response_model=Page[MemberOut])
async def club_members(
    club_id: int,
    status: str | None = Query(default=None, description="ACTIVE | INACTIVE | LEFT"),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[MemberOut]:
    async with acquire(pool) as conn:
        await _club_or_404(conn, club_id)
        rows = await fetch_many(conn, Q.CLUB_MEMBERS, (club_id, status, status))
    return Page(total=len(rows), items=[MemberOut(**r) for r in rows])


@router.post("/{club_id}/members", status_code=201)
async def join_club(
    club_id: int, payload: JoinClubIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> dict:
    """sp_join_club: creates or re-activates the membership."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_join_club", (payload.student_id, club_id))
    return rows[0]


@router.get("/{club_id}/officers", response_model=Page[OfficerOut])
async def club_officers(club_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Page[OfficerOut]:
    async with acquire(pool) as conn:
        await _club_or_404(conn, club_id)
        rows = await fetch_many(conn, Q.CLUB_OFFICERS, (club_id,))
    return Page(total=len(rows), items=[OfficerOut(**r) for r in rows])


@router.put("/{club_id}/officers", response_model=Page[dict])
async def assign_officer(
    club_id: int, payload: AssignOfficerIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> Page[dict]:
    """sp_assign_officer: appoints the role, demoting the previous holder."""
    async with acquire(pool) as conn:
        await _club_or_404(conn, club_id)
        rows = await call_proc(conn, "sp_assign_officer", (club_id, payload.student_id, payload.role))
    return Page(total=len(rows), items=rows)


@router.get("/{club_id}/events", response_model=Page[EventOut])
async def club_events(club_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Page[EventOut]:
    async with acquire(pool) as conn:
        await _club_or_404(conn, club_id)
        rows = await fetch_many(conn, Q.CLUB_EVENTS, (club_id,))
    return Page(total=len(rows), items=[EventOut(**r) for r in rows])


# ------------------------------------------------------------ memberships
@memberships_router.patch("/{membership_id}")
async def set_membership_status(
    membership_id: int, payload: MembershipStatusIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> dict:
    """Mark a member ACTIVE / INACTIVE (officers are demoted when deactivated)."""
    async with acquire(pool) as conn:
        if not await fetch_one(conn, Q.MEMBERSHIP_BY_ID, (membership_id,)):
            raise NotFoundError(f"Membership {membership_id} not found")
        await execute(
            conn, Q.MEMBERSHIP_SET_STATUS,
            (payload.membership_status, payload.membership_status, membership_id),
        )
        row = await fetch_one(conn, Q.MEMBERSHIP_BY_ID, (membership_id,))
    return row  # type: ignore[return-value]


@memberships_router.post("/{membership_id}/leave")
async def leave_club(membership_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    """sp_leave_club: status LEFT, vacates any officer position."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_leave_club", (membership_id,))
    return rows[0]
