"""Async repository helpers for the queries table."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Query


async def create_query(
    session: AsyncSession, *, request: str, company: str, ticker: str
) -> Dict[str, Any]:
    qid = str(uuid.uuid4())
    obj = Query(
        id=qid,
        request=request,
        company=company,
        ticker=ticker.upper(),
    )
    session.add(obj)
    await session.flush()
    return {
        "id": qid,
        "request": request,
        "company": company,
        "ticker": ticker.upper(),
        "created_at": (obj.created_at or datetime.utcnow()).isoformat(),
    }
