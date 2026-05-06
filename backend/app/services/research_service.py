"""Shared research pipeline: orchestration + persistence + PDF."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import orchestrate_research
from app.db import smoldb
from app.reports.generator import generate_report

logger = logging.getLogger(__name__)


def run_research_job(
    query: str,
    omit_sections: Optional[List[str]] = None,
    add_sections: Optional[List[str]] = None,
    request_label: Optional[str] = None,
    company_display: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run full research, persist to smoldb, generate PDF.
    Returns dict with success flag and either error or report fields.
    """
    try:
        smoldb.ensure_schema()
    except Exception as e:
        logger.exception("smoldb ensure_schema failed")
        return {"success": False, "error": f"Database unavailable: {e}"}

    result = orchestrate_research(
        query,
        omit_sections=omit_sections,
        add_sections=add_sections,
    )

    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Research failed"),
        }

    report_data = result.get("data", {})
    ticker = report_data.get("ticker")
    company_name = report_data.get("company_name")
    company_full = company_display or f"{company_name} ({ticker})"

    q_text = request_label or query
    query_record = smoldb.create_query(
        request=q_text, company=company_full, ticker=ticker
    )
    report_record = smoldb.create_report(
        query_id=query_record["id"],
        company=company_full,
        ticker=ticker,
        report_path="pending",
    )

    pdf_path = generate_report(report_data, report_record["id"])
    smoldb.update_report_path(report_record["id"], pdf_path)

    raw_data = report_data.get("raw_data", {})
    smoldb.create_report_data(
        report_id=report_record["id"],
        company_info=json.dumps(raw_data.get("company_info", {}), default=str),
        financial_data=json.dumps(raw_data.get("financials", {}), default=str),
        risk_data=json.dumps(raw_data.get("risks", {}), default=str),
        news_data=json.dumps(raw_data.get("news", {}), default=str),
        analysis=json.dumps(report_data.get("analysis", {}), default=str),
    )

    return {
        "success": True,
        "message": f"Research report generated for {company_name}",
        "report_id": report_record["id"],
        "report_path": pdf_path,
        "company": company_full,
        "ticker": ticker,
        "data": report_data,
    }
