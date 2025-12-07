from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
from app.schemas.request_schemas import ResearchRequest, ResearchResponse
from app.agents.orchestrator import orchestrate_research
from app.agents.tools import get_price_history, get_company_info
from app.utils.validation import resolve_company_to_ticker, parse_user_query
from app.reports.generator import generate_report
from app.db import file_storage as storage

router = APIRouter()


@router.post("/research", response_model=ResearchResponse)
async def create_research_report(request: ResearchRequest):
    try:
        result = orchestrate_research(request.query)
        
        if not result.get("success"):
            return ResearchResponse(
                success=False,
                message=result.get("error", "Research failed"),
                report_id=None,
                report_path=None,
                company=None
            )
        
        report_data = result.get("data", {})
        ticker = report_data.get("ticker")
        company_name = report_data.get("company_name")
        company_full = f"{company_name} ({ticker})"
        
        query_record = storage.create_query(request=request.query, company=company_full)
        report_record = storage.create_report(query_id=query_record["id"], company=company_full, report_path="pending")
        
        pdf_path = generate_report(report_data, report_record["id"])
        
        reports = storage.load_json(storage.REPORTS_FILE)
        for r in reports:
            if r["id"] == report_record["id"]:
                r["report_path"] = pdf_path
                break
        storage.save_json(storage.REPORTS_FILE, reports)
        
        raw_data = report_data.get("raw_data", {})
        storage.create_report_data(
            report_id=report_record["id"],
            company_info=json.dumps(raw_data.get("company_info", {}), default=str),
            financial_data=json.dumps(raw_data.get("financials", {}), default=str),
            risk_data=json.dumps(raw_data.get("risks", {}), default=str),
            news_data=json.dumps(raw_data.get("news", {}), default=str)
        )
        
        return ResearchResponse(
            success=True,
            message=f"Research report generated for {company_name}",
            report_id=report_record["id"],
            report_path=pdf_path,
            company=company_full
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/stream/{query}")
async def stream_research(query: str):
    """Stream research progress in real-time"""
    
    async def generate_progress() -> AsyncGenerator[str, None]:
        # Parse query
        yield f"data: {json.dumps({'step': 'parsing', 'message': 'Parsing your request...'})}\n\n"
        await asyncio.sleep(0.3)
        
        parsed = parse_user_query(query)
        company_query = parsed["company_query"]
        
        # Resolve ticker
        yield f"data: {json.dumps({'step': 'resolving', 'message': f'Finding ticker for {company_query}...'})}\n\n"
        await asyncio.sleep(0.3)
        
        ticker, company_name, error = resolve_company_to_ticker(company_query)
        
        if error:
            yield f"data: {json.dumps({'step': 'error', 'message': error})}\n\n"
            return
        
        yield f"data: {json.dumps({'step': 'resolved', 'message': f'Found {company_name} ({ticker})', 'ticker': ticker, 'company': company_name})}\n\n"
        await asyncio.sleep(0.3)
        
        # Fetch company info
        yield f"data: {json.dumps({'step': 'fetching_company', 'message': 'Fetching company information...'})}\n\n"
        company_info = get_company_info(ticker)
        await asyncio.sleep(0.2)
        
        # Fetch price data
        yield f"data: {json.dumps({'step': 'fetching_prices', 'message': 'Loading price history...'})}\n\n"
        price_data = get_price_history(ticker, "1y")
        await asyncio.sleep(0.2)
        
        yield f"data: {json.dumps({'step': 'complete', 'message': 'Data loaded', 'company_info': company_info, 'price_data': price_data})}\n\n"
    
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
        "price_data": price_data
    }


@router.get("/research/status/{report_id}")
async def get_research_status(report_id: int):
    report = storage.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "report_id": report["id"],
        "company": report["company"],
        "status": "completed" if report["report_path"] != "pending" else "processing",
        "created_at": report["created_at"],
        "report_path": report["report_path"]
    }
