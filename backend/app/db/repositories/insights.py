"""Async repository for PortfolioInsight — pgvector hybrid filter helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.models import PortfolioInsight


def _serialize(i: PortfolioInsight, *, distance: Optional[float] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "id": i.id,
        "user_id": i.user_id,
        "portfolio_metadata": i.portfolio_metadata,
        "insight_text": i.insight_text,
        "created_at": (i.created_at or datetime.utcnow()).isoformat(),
    }
    if distance is not None:
        out["distance"] = float(distance)
        out["similarity"] = float(1.0 - distance)
    return out


async def create_insight(
    session: AsyncSession,
    *,
    insight_text: str,
    embedding: Sequence[float],
    user_id: Optional[int] = None,
    portfolio_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    settings = get_settings()
    obj = PortfolioInsight(
        user_id=user_id if user_id is not None else settings.db_default_user_id,
        portfolio_metadata=portfolio_metadata,
        insight_text=insight_text,
        embedding=list(embedding),
    )
    session.add(obj)
    await session.flush()
    await session.refresh(obj)
    return _serialize(obj)


async def find_similar_insights(
    session: AsyncSession,
    *,
    embedding: Sequence[float],
    user_id: Optional[int] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Hybrid filter: filter by user_id first, then cosine distance ORDER BY.
    HNSW index on the embedding column makes this O(log n)."""
    settings = get_settings()
    uid = user_id if user_id is not None else settings.db_default_user_id

    distance = PortfolioInsight.embedding.cosine_distance(list(embedding))
    stmt = (
        select(PortfolioInsight, distance.label("distance"))
        .where(PortfolioInsight.user_id == uid)
        .order_by(distance.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [_serialize(row[0], distance=row[1]) for row in rows]
