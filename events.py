"""Event, registration, attendance and feedback endpoints."""
from __future__ import annotations

from datetime import date

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError, RuleViolationError
from app.db import acquire, call_proc, execute, fetch_many, fetch_one
from app.db import queries as Q
from app.models import (
    AttendanceIn, CancelResultOut, EventCreate, EventOut, EventUpdate, FeedbackIn,
    FeedbackOut, Message, Page, RegisterIn, RegistrationOut, RosterRow,
)
from app.routers.deps import get_db_pool, like

router = APIRouter(prefix="/events", tags=["events"])
registrations_router = APIRouter(prefix="/registrations", tags=["events"])
feedback_router = APIRouter(prefix="/feedback", tags=["events"])


async def _event_or_404(conn: aiomysql.Connection, event_id: int) -> dict:
    row = await fetch_one(conn, Q.EVENT_BY_ID, (event_id,))
    if not row:
        raise NotFoundError(f"Event {event_id} not found")
    return row


@router.get("", response_model=Page[EventOut])
async def list_events(
    status: str | None = Query(default=None, description="UPCOMING | ONGOING | COMPLETED | CANCELLED"),
    club_id: int | None = None,
    venue_id: int | None = None,
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[EventOut]:
    pattern = like(q)
    filt = (status, status, club_id, club_id, venue_id, venue_id,
            pattern, pattern, date_from, date_from, date_to, date_to)
    async with acquire(pool) as conn:
        total = (await fetch_one(conn, Q.EVENTS_COUNT, filt) or {"total": 0})["total"]
        rows = await fetch_many(conn, Q.EVENTS_LIST, filt + (limit, offset))
    return Page(total=total, items=[EventOut(**r) for r in rows])


@router.post("", response_model=EventOut, status_code=201)
async def create_event(payload: EventCreate, pool: aiomysql.Pool = Depends(get_db_pool)) -> EventOut:
    """Triggers validate venue capacity, venue clashes, active club and future date."""
    async with acquire(pool) as conn:
        new_id, _ = await execute(
            conn, Q.EVENT_INSERT,
            (payload.club_id, payload.venue_id, payload.event_name, payload.description,
             payload.event_date, payload.start_time, payload.end_time, payload.capacity,
             payload.registration_deadline),
        )
        row = await _event_or_404(conn, new_id)
    return EventOut(**row)


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> EventOut:
    async with acquire(pool) as conn:
        row = await _event_or_404(conn, event_id)
    return EventOut(**row)


@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int, payload: EventUpdate, pool: aiomysql.Pool = Depends(get_db_pool)
) -> EventOut:
    async with acquire(pool) as conn:
        current = await fetch_one(conn, Q.EVENT_BASE_BY_ID, (event_id,))
        if not current:
            raise NotFoundError(f"Event {event_id} not found")
        if current["event_status"] != "UPCOMING":
            raise RuleViolationError("Only upcoming events can be edited")
        current.update(payload.model_dump(exclude_unset=True))
        await execute(
            conn, Q.EVENT_UPDATE,
            (current["venue_id"], current["event_name"], current["description"],
             current["event_date"], current["start_time"], current["end_time"],
             current["capacity"], current["registration_deadline"], event_id),
        )
        row = await _event_or_404(conn, event_id)
    return EventOut(**row)


@router.delete("/{event_id}", response_model=Message)
async def delete_event(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Message:
    """Hard delete (registrations and feedback cascade). Prefer /cancel for real events."""
    async with acquire(pool) as conn:
        _, count = await execute(conn, Q.EVENT_DELETE, (event_id,))
    if count == 0:
        raise NotFoundError(f"Event {event_id} not found")
    return Message(detail="Event deleted")


@router.get("/{event_id}/summary")
async def event_summary(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    """sp_event_summary — stored procedure + stored functions."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_event_summary", (event_id,))
    return rows[0]


@router.post("/{event_id}/complete", response_model=dict)
async def complete_event(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    """sp_complete_event: unmarked attendees become ABSENT, event -> COMPLETED."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_complete_event", (event_id,))
    return rows[0]


@router.post("/{event_id}/cancel", response_model=dict)
async def cancel_event(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    """sp_cancel_event: cancels the event and every live registration."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_cancel_event", (event_id,))
    return rows[0]


# --------------------------------------------------------- registrations
@router.get("/{event_id}/roster", response_model=Page[RosterRow])
async def event_roster(
    event_id: int,
    status: str | None = Query(default=None, description="REGISTERED | WAITLISTED | CANCELLED"),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[RosterRow]:
    async with acquire(pool) as conn:
        await _event_or_404(conn, event_id)
        rows = await fetch_many(conn, Q.EVENT_ROSTER, (event_id, status, status))
    return Page(total=len(rows), items=[RosterRow(**r) for r in rows])


@router.post("/{event_id}/registrations", response_model=RegistrationOut, status_code=201)
async def register_for_event(
    event_id: int, payload: RegisterIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> RegistrationOut:
    """sp_register_for_event: REGISTERED when seats remain, otherwise WAITLISTED."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_register_for_event", (payload.student_id, event_id))
    return RegistrationOut(**rows[0])


@registrations_router.post("/{registration_id}/cancel", response_model=CancelResultOut)
async def cancel_registration(
    registration_id: int, pool: aiomysql.Pool = Depends(get_db_pool)
) -> CancelResultOut:
    """sp_cancel_registration: frees the seat and promotes the first waitlisted student."""
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_cancel_registration", (registration_id,))
    return CancelResultOut(**rows[0])


@registrations_router.patch("/{registration_id}/attendance", response_model=dict)
async def mark_attendance(
    registration_id: int, payload: AttendanceIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> dict:
    async with acquire(pool) as conn:
        rows = await call_proc(conn, "sp_mark_attendance", (registration_id, payload.attendance))
    return rows[0]


# --------------------------------------------------------------- feedback
@router.get("/{event_id}/feedback", response_model=Page[FeedbackOut])
async def event_feedback(event_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Page[FeedbackOut]:
    async with acquire(pool) as conn:
        await _event_or_404(conn, event_id)
        rows = await fetch_many(conn, Q.EVENT_FEEDBACK, (event_id,))
    return Page(total=len(rows), items=[FeedbackOut(**r) for r in rows])


@router.post("/{event_id}/feedback", response_model=FeedbackOut, status_code=201)
async def submit_feedback(
    event_id: int, payload: FeedbackIn, pool: aiomysql.Pool = Depends(get_db_pool)
) -> FeedbackOut:
    """sp_submit_feedback: only students marked PRESENT; resubmitting updates."""
    async with acquire(pool) as conn:
        rows = await call_proc(
            conn, "sp_submit_feedback",
            (payload.student_id, event_id, payload.rating, payload.comments),
        )
    return FeedbackOut(**rows[0])


@feedback_router.get("/recent", response_model=Page[FeedbackOut])
async def recent_feedback(
    limit: int = Query(default=10, ge=1, le=100), pool: aiomysql.Pool = Depends(get_db_pool)
) -> Page[FeedbackOut]:
    async with acquire(pool) as conn:
        rows = await fetch_many(conn, Q.RECENT_FEEDBACK, (limit,))
    return Page(total=len(rows), items=[FeedbackOut(**r) for r in rows])
