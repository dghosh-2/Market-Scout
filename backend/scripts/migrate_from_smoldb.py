"""One-off data migration: smoldb (HTTP SQLite) -> Postgres via SQLAlchemy.

Usage:
    cd backend
    python scripts/migrate_from_smoldb.py

Requirements:
    SMOLDB_KEY, SMOLDB_URL, and DATABASE_URL must be present in .env.
    The Postgres schema (`migrations/0001_initial.sql`) must already be applied.

This is intentionally NOT run automatically. It is safe to re-run; existing rows
are skipped on PK conflict.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

import requests
from sqlalchemy import select

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.config.settings import get_settings  # noqa: E402
from app.db.database import session_scope  # noqa: E402
from app.db.models import (  # noqa: E402
    PortfolioHolding,
    Query,
    Report,
    ReportData,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _smoldb_query(sql: str) -> List[Dict[str, Any]]:
    settings = get_settings()
    smoldb_url = os.environ.get("SMOLDB_URL", "").rstrip("/")
    smoldb_key = os.environ.get("SMOLDB_KEY", "")
    if not smoldb_url or not smoldb_key:
        raise RuntimeError("SMOLDB_URL and SMOLDB_KEY must be set in the environment.")
    resp = requests.post(
        f"{smoldb_url}/query",
        headers={"x-api-key": smoldb_key, "Content-Type": "application/json"},
        json={"sql": sql},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("rows", []) or []


def _norm(row: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k).lower(): v for k, v in row.items()}


def _maybe_json(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


async def _migrate_queries() -> None:
    rows = [_norm(r) for r in _smoldb_query("SELECT * FROM queries")]
    logger.info("Migrating %d queries", len(rows))
    async with session_scope() as session:
        for r in rows:
            qid = r.get("id")
            existing = await session.execute(select(Query).where(Query.id == qid))
            if existing.scalar_one_or_none():
                continue
            session.add(
                Query(
                    id=qid,
                    request=r.get("request") or "",
                    company=r.get("company") or "",
                    ticker=(r.get("ticker") or "").upper(),
                )
            )


async def _migrate_reports() -> None:
    rows = [_norm(r) for r in _smoldb_query("SELECT * FROM reports")]
    logger.info("Migrating %d reports", len(rows))
    async with session_scope() as session:
        for r in rows:
            rid = r.get("id")
            existing = await session.execute(select(Report).where(Report.id == rid))
            if existing.scalar_one_or_none():
                continue
            session.add(
                Report(
                    id=rid,
                    query_id=r.get("query_id"),
                    company=r.get("company") or "",
                    ticker=(r.get("ticker") or "").upper(),
                    report_path=r.get("report_path") or "",
                    version=int(r.get("version") or 1),
                )
            )


async def _migrate_report_data() -> None:
    rows = [_norm(r) for r in _smoldb_query("SELECT * FROM report_data")]
    logger.info("Migrating %d report_data rows", len(rows))
    async with session_scope() as session:
        for r in rows:
            rid = r.get("report_id")
            existing = await session.execute(select(ReportData).where(ReportData.report_id == rid))
            if existing.scalar_one_or_none():
                continue
            session.add(
                ReportData(
                    report_id=rid,
                    company_info=_maybe_json(r.get("company_info")),
                    financial_data=_maybe_json(r.get("financial_data")),
                    risk_data=_maybe_json(r.get("risk_data")),
                    news_data=_maybe_json(r.get("news_data")),
                    analysis=_maybe_json(r.get("analysis")),
                )
            )


async def _migrate_portfolio() -> None:
    rows = [_norm(r) for r in _smoldb_query("SELECT * FROM portfolio")]
    logger.info("Migrating %d portfolio rows", len(rows))
    async with session_scope() as session:
        for r in rows:
            ticker = (r.get("ticker") or "").upper()
            if not ticker:
                continue
            existing = await session.execute(
                select(PortfolioHolding).where(PortfolioHolding.ticker == ticker)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(
                PortfolioHolding(
                    ticker=ticker,
                    shares=float(r.get("shares") or 0),
                    purchase_price=(
                        float(r.get("purchase_price"))
                        if r.get("purchase_price") not in (None, "")
                        else None
                    ),
                    company_name=r.get("company_name") or ticker,
                    holding_id=r.get("holding_id") or ticker,
                )
            )


async def main() -> None:
    await _migrate_queries()
    await _migrate_reports()
    await _migrate_report_data()
    await _migrate_portfolio()
    logger.info("Migration complete")


if __name__ == "__main__":
    asyncio.run(main())
