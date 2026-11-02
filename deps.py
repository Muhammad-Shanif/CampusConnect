"""Router dependencies and tiny shared helpers."""
from __future__ import annotations

import aiomysql
from fastapi import Request


def get_db_pool(request: Request) -> aiomysql.Pool:
    """The global aiomysql pool stored on app.state by the lifespan."""
    return request.app.state.pool


def like(term: str | None) -> str | None:
    """Wrap a search term for LIKE; None stays None (filter disabled)."""
    term = (term or "").strip()
    return f"%{term}%" if term else None
