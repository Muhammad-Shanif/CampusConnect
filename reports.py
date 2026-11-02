"""Report endpoints — thin wrappers over the SQL views."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.db import acquire, fetch_many, fetch_one
from app.db import queries as Q
from app.models import Page
from app.routers.deps import get_db_pool

router = APIRouter(prefix="/reports", tags=["reports"])


async def _page(pool: aiomysql.Pool, sql: str, args: tuple = ()) -> Page[dict]:
    async with acquire(pool) as conn:
        rows = await fetch_many(conn, sql, args or None)
    return Page(total=len(rows), items=rows)


@router.get("/dashboard")
async def dashboard(pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    """Headline numbers for the home page."""
    async with acquire(pool) as conn:
        return await fetch_one(conn, Q.DASHBOARD_TOTALS) or {}


@router.get("/upcoming", response_model=Page[dict])
async def upcoming(limit: int = Query(default=6, ge=1, le=50), pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.UPCOMING_EVENTS, (limit,))


@router.get("/club-membership", response_model=Page[dict])
async def club_membership(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.CLUB_MEMBERSHIP_COUNTS)


@router.get("/club-activity", response_model=Page[dict])
async def club_activity(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.CLUB_ACTIVITY)


@router.get("/officers", response_model=Page[dict])
async def officers(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.ALL_OFFICERS)


@router.get("/event-popularity", response_model=Page[dict])
async def event_popularity(limit: int = Query(default=10, ge=1, le=100), pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.EVENT_POPULARITY, (limit,))


@router.get("/event-attendance", response_model=Page[dict])
async def event_attendance(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.EVENT_ATTENDANCE)


@router.get("/feedback-summary", response_model=Page[dict])
async def feedback_summary(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.FEEDBACK_SUMMARY)


@router.get("/top-students", response_model=Page[dict])
async def top_students(limit: int = Query(default=10, ge=1, le=100), pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.STUDENT_ACTIVITY_TOP, (limit,))


@router.get("/department-participation", response_model=Page[dict])
async def department_participation(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.DEPARTMENT_PARTICIPATION)


@router.get("/venue-utilisation", response_model=Page[dict])
async def venue_utilisation(pool: aiomysql.Pool = Depends(get_db_pool)):
    return await _page(pool, Q.VENUE_UTILISATION)
