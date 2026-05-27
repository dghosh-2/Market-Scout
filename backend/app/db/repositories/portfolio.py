"""Async repository helpers for the portfolio table."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PortfolioHolding


def _serialize(h: PortfolioHolding) -> Dict[str, Any]:
    return {
        "ticker": h.ticker,
        "shares": float(h.shares),
        "purchase_price": float(h.purchase_price) if h.purchase_price is not None else None,
        "company_name": h.company_name or h.ticker,
        "holding_id": h.holding_id or h.ticker,
        "created_at": (h.created_at or datetime.utcnow()).isoformat(),
        "updated_at": (h.updated_at or datetime.utcnow()).isoformat(),
    }


async def list_all(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(
        select(PortfolioHolding).order_by(PortfolioHolding.ticker.asc())
    )
    return [_serialize(h) for h in result.scalars().all()]


async def get(session: AsyncSession, ticker: str) -> Optional[Dict[str, Any]]:
    obj = await session.get(PortfolioHolding, ticker.upper())
    return _serialize(obj) if obj else None


async def insert(
    session: AsyncSession,
    *,
    ticker: str,
    shares: float,
    company_name: Optional[str],
    holding_id: str,
    purchase_price: Optional[float] = None,
) -> Dict[str, Any]:
    obj = PortfolioHolding(
        ticker=ticker.upper(),
        shares=float(shares),
        purchase_price=float(purchase_price) if purchase_price is not None else None,
        company_name=company_name or ticker.upper(),
        holding_id=holding_id,
    )
    session.add(obj)
    await session.flush()
    await session.refresh(obj)
    return _serialize(obj)


async def update_shares(
    session: AsyncSession, *, ticker: str, shares: float
) -> Optional[Dict[str, Any]]:
    obj = await session.get(PortfolioHolding, ticker.upper())
    if obj is None:
        return None
    obj.shares = float(shares)
    await session.flush()
    await session.refresh(obj)
    return _serialize(obj)


async def delete(session: AsyncSession, ticker: str) -> bool:
    obj = await session.get(PortfolioHolding, ticker.upper())
    if obj is None:
        return False
    await session.delete(obj)
    await session.flush()
    return True
