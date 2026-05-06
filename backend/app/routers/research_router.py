from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator, List, Optional

from app.schemas.request_schemas import ResearchRequest, ResearchResponse
from app.agents.tools import get_price_history, get_company_info
from app.utils.validation import resolve_company_to_ticker, parse_user_query
from app.db import smoldb
from app.services.research_service import run_research_job
from app.limiter import limiter

router = APIRouter()


def _split_csv(val: Optional[str]) -> Optional[List[str]]:
    if not val or not val.strip():
        return None
    return [s.strip() for s in val.split(",") if s.strip()]


@router.post("/research", response_model=ResearchResponse)
@limiter.limit("5/minute")
async def create_research_report(request: Request, body: ResearchRequest):
    try:
        result = await asyncio.to_thread(
            run_research_job,
            body.query,
            body.omit_sections,
            body.add_sections,
        )

        if not result.get("success"):
            return ResearchResponse(
                success=False,
                message=result.get("error", "Research failed"),
                report_id=None,
                report_path=None,
                company=None,
            )

        return ResearchResponse(
            success=True,
            message=result.get("message", "OK"),
            report_id=result.get("report_id"),
            report_path=result.get("report_path"),
            company=result.get("company"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/stream/{query}")
async def stream_research(
    query: str,
    omit_sections: Optional[str] = Query(None, description="Comma-separated sections to omit"),
    add_sections: Optional[str] = Query(None, description="Comma-separated extra topics"),
):
    """Stream research progress; final event includes report_id when generation completes."""

    omit_list = _split_csv(omit_sections)
    add_list = _split_csv(add_sections)

    async def generate_progress() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'step': 'parsing', 'message': 'Parsing your request...'})}\n\n"
        await asyncio.sleep(0.2)

        parsed = parse_user_query(query)
        company_query = parsed["company_query"]

        yield f"data: {json.dumps({'step': 'resolving', 'message': f'Finding ticker for {company_query}...'})}\n\n"
        await asyncio.sleep(0.2)

        ticker, company_name, error = resolve_company_to_ticker(company_query)

        if error:
            yield f"data: {json.dumps({'step': 'error', 'message': error})}\n\n"
            return

        yield f"data: {json.dumps({'step': 'resolved', 'message': f'Found {company_name} ({ticker})', 'ticker': ticker, 'company_name': company_name})}\n\n"
        await asyncio.sleep(0.2)

        yield f"data: {json.dumps({'step': 'fetching_company', 'message': 'Fetching company information...'})}\n\n"
        company_info = get_company_info(ticker)
        await asyncio.sleep(0.15)

        yield f"data: {json.dumps({'step': 'fetching_prices', 'message': 'Loading price history...'})}\n\n"
        price_data = get_price_history(ticker, "1y")
        await asyncio.sleep(0.15)

        yield f"data: {json.dumps({'step': 'generating', 'message': 'Generating analysis and PDF...'})}\n\n"

        try:
            final = await asyncio.to_thread(
                run_research_job, query, omit_list, add_list
            )
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"
            return

        if not final.get("success"):
            yield f"data: {json.dumps({'step': 'error', 'message': final.get('error', 'Research failed')})}\n\n"
            return

        payload = {
            "step": "complete",
            "message": "Report ready",
            "report_id": final.get("report_id"),
            "report_path": final.get("report_path"),
            "company": final.get("company"),
            "ticker": final.get("ticker"),
            "company_info": company_info,
            "price_data": price_data,
        }
        yield f"data: {json.dumps(payload, default=str)}\n\n"

    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.get("/research/preview/{query}")
async def preview_research(query: str):
    """Get quick preview data without full report"""
    parsed = parse_user_query(query)
    ticker, company_name, error = resolve_company_to_ticker(parsed["company_query"])

    if error:
        raise HTTPException(status_code=400, detail=error)

    company_info = get_company_info(ticker)
    price_data = get_price_history(ticker, "1y")

    return {
        "ticker": ticker,
        "company_name": company_name,
        "company_info": company_info,
        "price_data": price_data,
    }


@router.get("/research/status/{report_id}")
async def get_research_status(report_id: str):
    smoldb.ensure_schema()
    report = smoldb.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    r = {k.lower(): v for k, v in report.items()}
    path = r.get("report_path", "")
    return {
        "report_id": r.get("id"),
        "company": r.get("company"),
        "ticker": r.get("ticker"),
        "status": "completed" if path and path != "pending" else "processing",
        "created_at": r.get("created_at"),
        "report_path": path,
    }
