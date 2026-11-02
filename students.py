"""Student endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError
from app.db import acquire, execute, fetch_many, fetch_one
from app.db import queries as Q
from app.models import Message, Page, StudentCreate, StudentOut, StudentUpdate
from app.models.event import StudentRegistrationOut
from app.routers.deps import get_db_pool, like

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentOut])
async def list_students(
    q: str | None = Query(default=None, description="Search name or email"),
    department: str | None = None,
    year: int | None = Query(default=None, ge=1, le=6),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> Page[StudentOut]:
    pattern = like(q)
    filt = (pattern, pattern, pattern, department, department, year, year)
    async with acquire(pool) as conn:
        total = (await fetch_one(conn, Q.STUDENTS_COUNT, filt) or {"total": 0})["total"]
        rows = await fetch_many(conn, Q.STUDENTS_LIST, filt + (limit, offset))
    return Page(total=total, items=[StudentOut(**r) for r in rows])


@router.get("/meta/departments", response_model=list[str])
async def list_departments(pool: aiomysql.Pool = Depends(get_db_pool)) -> list[str]:
    async with acquire(pool) as conn:
        rows = await fetch_many(conn, Q.DEPARTMENTS)
    return [r["department"] for r in rows]


@router.post("", response_model=StudentOut, status_code=201)
async def create_student(
    payload: StudentCreate, pool: aiomysql.Pool = Depends(get_db_pool)
) -> StudentOut:
    async with acquire(pool) as conn:
        new_id, _ = await execute(
            conn,
            Q.STUDENT_INSERT,
            (payload.name, payload.email, payload.phone, payload.department,
             payload.year_of_study, payload.enrollment_date),
        )
        row = await fetch_one(conn, Q.STUDENT_BY_ID, (new_id,))
    return StudentOut(**row)  # type: ignore[arg-type]


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> StudentOut:
    async with acquire(pool) as conn:
        row = await fetch_one(conn, Q.STUDENT_BY_ID, (student_id,))
    if not row:
        raise NotFoundError(f"Student {student_id} not found")
    return StudentOut(**row)


@router.put("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: int, payload: StudentUpdate, pool: aiomysql.Pool = Depends(get_db_pool)
) -> StudentOut:
    async with acquire(pool) as conn:
        current = await fetch_one(conn, Q.STUDENT_BASE_BY_ID, (student_id,))
        if not current:
            raise NotFoundError(f"Student {student_id} not found")
        current.update(payload.model_dump(exclude_unset=True))
        await execute(
            conn,
            Q.STUDENT_UPDATE,
            (current["name"], current["email"], current["phone"], current["department"],
             current["year_of_study"], student_id),
        )
        row = await fetch_one(conn, Q.STUDENT_BY_ID, (student_id,))
    return StudentOut(**row)  # type: ignore[arg-type]


@router.delete("/{student_id}", response_model=Message)
async def delete_student(student_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Message:
    async with acquire(pool) as conn:
        _, count = await execute(conn, Q.STUDENT_DELETE, (student_id,))
    if count == 0:
        raise NotFoundError(f"Student {student_id} not found")
    return Message(detail="Student deleted")


@router.get("/{student_id}/clubs", response_model=Page[dict])
async def student_clubs(student_id: int, pool: aiomysql.Pool = Depends(get_db_pool)) -> Page[dict]:
    async with acquire(pool) as conn:
        if not await fetch_one(conn, Q.STUDENT_BASE_BY_ID, (student_id,)):
            raise NotFoundError(f"Student {student_id} not found")
        rows = await fetch_many(conn, Q.STUDENT_MEMBERSHIPS, (student_id,))
    return Page(total=len(rows), items=rows)


@router.get("/{student_id}/registrations", response_model=Page[StudentRegistrationOut])
async def student_registrations(
    student_id: int, pool: aiomysql.Pool = Depends(get_db_pool)
) -> Page[StudentRegistrationOut]:
    async with acquire(pool) as conn:
        if not await fetch_one(conn, Q.STUDENT_BASE_BY_ID, (student_id,)):
            raise NotFoundError(f"Student {student_id} not found")
        rows = await fetch_many(conn, Q.STUDENT_REGISTRATIONS, (student_id,))
    return Page(total=len(rows), items=[StudentRegistrationOut(**r) for r in rows])
