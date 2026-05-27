"""Async repository helpers for reports + report_data."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report, ReportData


def _serialize_report(r: Report) -> Dict[str, Any]:
    return {
        "id": r.id,
        "query_id": r.query_id,
        "company": r.company,
        "ticker": r.ticker,
        "report_path": r.report_path,
        "version": r.version,
        "created_at": (r.created_at or datetime.utcnow()).isoformat(),
    }


def _serialize_report_data(d: ReportData) -> Dict[str, Any]:
    return {
        "report_id": d.report_id,
        "company_info": d.company_info,
        "financial_data": d.financial_data,
        "risk_data": d.risk_data,
        "news_data": d.news_data,
        "analysis": d.analysis,
    }


async def _next_version_for_ticker(session: AsyncSession, ticker: str) -> int:
    result = await session.execute(
        select(func.count()).select_from(Report).where(Report.ticker == ticker.upper())
    )
    return int(result.scalar_one() or 0) + 1


async def create_report(
    session: AsyncSession,
    *,
    query_id: str,
    company: str,
    ticker: str,
    report_path: str,
) -> Dict[str, Any]:
    version = await _next_version_for_ticker(session, ticker)
    rid = str(uuid.uuid4())
    obj = Report(
        id=rid,
        query_id=query_id,
        company=company,
        ticker=ticker.upper(),
        report_path=report_path,
        version=version,
    )
    session.add(obj)
    await session.flush()
    return _serialize_report(obj)


async def update_report_path(
    session: AsyncSession, *, report_id: str, report_path: str
) -> None:
    obj = await session.get(Report, report_id)
    if obj is None:
        return
    obj.report_path = report_path
    await session.flush()


async def get_report(session: AsyncSession, report_id: str) -> Optional[Dict[str, Any]]:
    obj = await session.get(Report, report_id)
    return _serialize_report(obj) if obj else None


async def get_reports_by_ticker(
    session: AsyncSession, ticker: str
) -> List[Dict[str, Any]]:
    result = await session.execute(
        select(Report)
        .where(Report.ticker == ticker.upper())
        .order_by(Report.created_at.desc())
    )
    return [_serialize_report(r) for r in result.scalars().all()]


async def get_reports_by_company_substring(
    session: AsyncSession, company: str
) -> List[Dict[str, Any]]:
    needle = company.strip().lower().replace("%", "")
    if not needle:
        return []
    result = await session.execute(
        select(Report)
        .where(func.lower(Report.company).like(f"%{needle}%"))
        .order_by(Report.created_at.desc())
    )
    return [_serialize_report(r) for r in result.scalars().all()]


async def get_reports_for_identifier(
    session: AsyncSession, company_or_ticker: str
) -> List[Dict[str, Any]]:
    ticker = company_or_ticker.strip().upper()
    by_ticker = await get_reports_by_ticker(session, ticker)
    if by_ticker:
        return by_ticker
    return await get_reports_by_company_substring(session, company_or_ticker)


async def get_all_reports(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(select(Report).order_by(Report.created_at.desc()))
    return [_serialize_report(r) for r in result.scalars().all()]


async def get_grouped_reports(
    session: AsyncSession,
) -> Dict[str, List[Dict[str, Any]]]:
    reports = await get_all_reports(session)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in reports:
        company = r.get("company") or "Unknown"
        grouped.setdefault(company, []).append(r)
    return grouped


async def create_report_data(
    session: AsyncSession,
    *,
    report_id: str,
    company_info: Optional[Dict[str, Any]] = None,
    financial_data: Optional[Dict[str, Any]] = None,
    risk_data: Optional[Dict[str, Any]] = None,
    news_data: Optional[Dict[str, Any]] = None,
    analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = ReportData(
        report_id=report_id,
        company_info=company_info,
        financial_data=financial_data,
        risk_data=risk_data,
        news_data=news_data,
        analysis=analysis,
    )
    session.add(obj)
    await session.flush()
    return {"report_id": report_id}


async def get_report_data(
    session: AsyncSession, report_id: str
) -> Optional[Dict[str, Any]]:
    obj = await session.get(ReportData, report_id)
    return _serialize_report_data(obj) if obj else None
