from fastapi import APIRouter, HTTPException
from app.schemas.request_schemas import FeedbackRequest, FeedbackResponse
from app.db import smoldb
from app.services.research_service import run_research_job
import asyncio

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on a report to generate a new version"""
    smoldb.ensure_schema()
    original_report = smoldb.get_report(request.report_id)
    if not original_report:
        raise HTTPException(status_code=404, detail="Report not found")

    r = {k.lower(): v for k, v in original_report.items()}
    company = r.get("company", "")
    ticker = r.get("ticker") or ""

    if not ticker and "(" in company and ")" in company:
        ticker = company.split("(")[-1].replace(")", "").strip()

    if not ticker:
        raise HTTPException(status_code=400, detail="Could not resolve ticker for report")

    new_query = f"{ticker} - {request.feedback}"

    try:
        result = await asyncio.to_thread(
            run_research_job,
            new_query,
            None,
            None,
            f"Feedback on {request.report_id}: {request.feedback}",
            company,
        )

        if not result.get("success"):
            return FeedbackResponse(
                success=False,
                message=result.get("error", "Failed to generate new report"),
                new_report_id=None,
                new_report_path=None,
            )

        return FeedbackResponse(
            success=True,
            message="New report generated based on feedback",
            new_report_id=result.get("report_id"),
            new_report_path=result.get("report_path"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
