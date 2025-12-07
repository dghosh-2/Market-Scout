from fastapi import APIRouter, HTTPException
import json
from app.schemas.request_schemas import FeedbackRequest, FeedbackResponse
from app.db import file_storage as storage
from app.agents.orchestrator import orchestrate_research
from app.reports.generator import generate_report

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on a report to generate a new version"""
    
    # Get original report
    original_report = storage.get_report(request.report_id)
    if not original_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get original report data
    original_data = storage.get_report_data(request.report_id)
    
    company = original_report.get("company", "")
    
    # Extract ticker from company string (format: "Company Name (TICKER)")
    ticker = ""
    if "(" in company and ")" in company:
        ticker = company.split("(")[-1].replace(")", "").strip()
    
    # Create new query with feedback
    new_query = f"{ticker} - {request.feedback}"
    
    try:
        result = orchestrate_research(new_query)
        
        if not result.get("success"):
            return FeedbackResponse(
                success=False,
                message=result.get("error", "Failed to generate new report"),
                new_report_id=None,
                new_report_path=None
            )
        
        report_data = result.get("data", {})
        
        # Create new query record
        query_record = storage.create_query(
            request=f"Feedback on {request.report_id}: {request.feedback}",
            company=company
        )
        
        # Create new report
        report_record = storage.create_report(
            query_id=query_record["id"],
            company=company,
            report_path="pending"
        )
        
        # Generate PDF
        pdf_path = generate_report(report_data, report_record["id"])
        
        # Update report path
        reports = storage.load_json(storage.REPORTS_FILE)
        for r in reports:
            if r["id"] == report_record["id"]:
                r["report_path"] = pdf_path
                break
        storage.save_json(storage.REPORTS_FILE, reports)
        
        # Store raw data
        raw_data = report_data.get("raw_data", {})
        storage.create_report_data(
            report_id=report_record["id"],
            company_info=json.dumps(raw_data.get("company_info", {}), default=str),
            financial_data=json.dumps(raw_data.get("financials", {}), default=str),
            risk_data=json.dumps(raw_data.get("risks", {}), default=str),
            news_data=json.dumps(raw_data.get("news", {}), default=str)
        )
        
        return FeedbackResponse(
            success=True,
            message=f"New report generated based on feedback",
            new_report_id=report_record["id"],
            new_report_path=pdf_path
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
