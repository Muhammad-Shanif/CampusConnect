"""Venue endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends

from app.core.errors import NotFoundError
from app.db import acquire, execute, fetch_many, fetch_one
from app.db import queries as Q
from app.models import EventOut, Message, Page, VenueCreate, VenueOut, VenueUpdate
from app.routers.deps import get_db_pool, like

router = APIRouter(prefix="/venues", tags=["venues"])


async def _venue_or_404(conn: aiomysql.Connection, venue_id: int) -> dict:
    row = await fetch_one(conn, Q.VENUE_BY_ID, (venue_id,))
    if not row:
        raise NotFoundError(f"Venue {venue_id} not found")
    return row


@router.get("", response_model=Page[VenueOut])
async def list_venues(
    q: str | None = None,
    venue_type: str | None = None,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[VenueOut]:
    pattern = like(q)
    async with acquire(pool) as conn:
        rows = await fetch_many(
            conn, Q.VENUES_LIST, (pattern, pattern, pattern, venue_type, venue_type)
        )
    return Page(total=len(rows), items=[VenueOut(**r) for r in rows])


@router.post("", response_model=VenueOut, status_code=201)
async def create_venue(payload: VenueCreate, pool: aiomysql.Pool = Depends(get_db_pool)) -> VenueOut:
    async with acquire(pool) as conn:
        new_id, _ = await execute(
            conn, Q.VENUE_INSERT,
            (payload.venue_name, payload.building, payload.room_number,
             payload.capacity, payload.venue_type),
        )
        row = await _venue_or_404(conn, new_id)
    return VenueOut(**row)


@router.get("/{venue_id}", response_model=VenueOut)
async def get_venue(venue_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> VenueOut:
    async with acquire(pool) as conn:
        row = await _venue_or_404(conn, venue_id)
    return VenueOut(**row)


@router.put("/{venue_id}", response_model=VenueOut)
async def update_venue(
    venue_id: int, payload: VenueUpdate, pool: aiomysql.Pool = Depends(get_db_pool)
) -> VenueOut:
    async with acquire(pool) as conn:
        current = await fetch_one(conn, Q.VENUE_BASE_BY_ID, (venue_id,))
        if not current:
            raise NotFoundError(f"Venue {venue_id} not found")
        current.update(payload.model_dump(exclude_unset=True))
        await execute(
            conn, Q.VENUE_UPDATE,
            (current["venue_name"], current["building"], current["room_number"],
             current["capacity"], current["venue_type"], venue_id),
        )
        row = await _venue_or_404(conn, venue_id)
    return VenueOut(**row)


@router.delete("/{venue_id}", response_model=Message)
async def delete_venue(venue_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Message:
    """409 when events are still scheduled there (FK RESTRICT)."""
    async with acquire(pool) as conn:
        _, count = await execute(conn, Q.VENUE_DELETE, (venue_id,))
    if count == 0:
        raise NotFoundError(f"Venue {venue_id} not found")
    return Message(detail="Venue deleted")


@router.get("/{venue_id}/events", response_model=Page[EventOut])
async def venue_events(venue_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Page[EventOut]:
    async with acquire(pool) as conn:
        await _venue_or_404(conn, venue_id)
        rows = await fetch_many(conn, Q.VENUE_EVENTS, (venue_id,))
    return Page(total=len(rows), items=[EventOut(**r) for r in rows])
