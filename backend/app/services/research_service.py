"""Async research pipeline: cache lookup -> graph -> persist -> PDF -> cache write."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import orchestrate_research
from app.cache.semantic_cache import get_cache
from app.db.database import session_scope
from app.db.repositories import queries as queries_repo
from app.db.repositories import reports as reports_repo
from app.reports.generator import generate_report
from app.telemetry.langfuse_client import observe, update_current_observation

logger = logging.getLogger(__name__)


@observe(name="run_research_job")
async def run_research_job(
    query: str,
    omit_sections: Optional[List[str]] = None,
    add_sections: Optional[List[str]] = None,
    request_label: Optional[str] = None,
    company_display: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full research pipeline with semantic caching + persistence."""
    cache = get_cache()

    cached = await cache.lookup(query)
    if cached and isinstance(cached, dict):
        update_current_observation(cache_hit=True)
        meta = cached.get("_cache", {}) or {}
        return {
            "success": True,
            "message": (
                f"Cached report (similarity={meta.get('similarity', 0):.2f})"
                if meta.get("similarity") is not None
                else "Cached report"
            ),
            "report_id": cached.get("report_id"),
            "report_path": cached.get("report_path"),
            "company": cached.get("company"),
            "ticker": cached.get("ticker"),
            "data": cached.get("data") or cached,
            "cache": meta,
        }

    update_current_observation(cache_hit=False)

    result = await orchestrate_research(
        query, omit_sections=omit_sections, add_sections=add_sections
    )
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Research failed")}

    report_data = result.get("data", {}) or {}
    ticker = report_data.get("ticker")
    company_name = report_data.get("company_name")
    company_full = company_display or f"{company_name} ({ticker})"
    q_text = request_label or query

    try:
        async with session_scope() as session:
            query_record = await queries_repo.create_query(
                session, request=q_text, company=company_full, ticker=ticker
            )
            report_record = await reports_repo.create_report(
                session,
                query_id=query_record["id"],
                company=company_full,
                ticker=ticker,
                report_path="pending",
            )
    except Exception as e:
        logger.exception("Persistence (queries/reports) failed")
        return {"success": False, "error": f"Database write failed: {e}"}

    try:
        pdf_path = await asyncio.to_thread(generate_report, report_data, report_record["id"])
    except Exception as e:
        logger.exception("PDF generation failed")
        return {"success": False, "error": f"PDF generation failed: {e}"}

    try:
        async with session_scope() as session:
            await reports_repo.update_report_path(
                session, report_id=report_record["id"], report_path=pdf_path
            )
            raw_data = report_data.get("raw_data", {}) or {}
            await reports_repo.create_report_data(
                session,
                report_id=report_record["id"],
                company_info=raw_data.get("company_info"),
                financial_data=raw_data.get("financials"),
                risk_data=raw_data.get("risks"),
                news_data=raw_data.get("news"),
                analysis=report_data.get("analysis"),
            )
    except Exception as e:
        logger.exception("Persistence (report_data) failed")

    cache_payload = {
        "report_id": report_record["id"],
        "report_path": pdf_path,
        "company": company_full,
        "ticker": ticker,
        "data": report_data,
    }
    try:
        await cache.write(query, cache_payload)
    except Exception as e:  # never let cache writes break the response
        logger.debug("cache write skipped: %s", e)

    return {
        "success": True,
        "message": f"Research report generated for {company_name}",
        "report_id": report_record["id"],
        "report_path": pdf_path,
        "company": company_full,
        "ticker": ticker,
        "data": report_data,
        "cache": {"hit": False},
    }
