"""Health probes."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends

from app.db import acquire, fetch_one
from app.db import queries as Q
from app.routers.deps import get_db_pool

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(pool: aiomysql.Pool = Depends(get_db_pool)) -> dict:
    async with acquire(pool) as conn:
        row = await fetch_one(conn, Q.PING)
    return {"status": "ok", "database": "up" if row else "down"}
