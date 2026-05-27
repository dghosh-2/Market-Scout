from fastapi import APIRouter, HTTPException

from app.db.database import session_scope
from app.db.repositories import reports as reports_repo

router = APIRouter()


@router.get("/papers")
async def get_all_papers():
    """All reports grouped by company."""
    async with session_scope() as session:
        grouped = await reports_repo.get_grouped_reports(session)

    result = []
    for company, reports in grouped.items():
        result.append({
            "company": company,
            "report_count": len(reports),
            "reports": sorted(
                reports,
                key=lambda x: x.get("created_at") or "",
                reverse=True,
            ),
        })

    return sorted(
        result,
        key=lambda x: x["reports"][0]["created_at"] if x["reports"] else "",
        reverse=True,
    )


@router.get("/papers/{company}")
async def get_company_papers(company: str):
    """All reports for a ticker (exact) or company name substring."""
    async with session_scope() as session:
        reports = await reports_repo.get_reports_for_identifier(session, company)
    if not reports:
        raise HTTPException(status_code=404, detail=f"No reports found for {company}")
    return {
        "company": company,
        "reports": sorted(
            reports,
            key=lambda x: x.get("created_at") or "",
            reverse=True,
        ),
    }


@router.get("/papers/report/{report_id}")
async def get_paper(report_id: str):
    async with session_scope() as session:
        report = await reports_repo.get_report(session, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        data = await reports_repo.get_report_data(session, report_id)
    return {"report": report, "data": data or {}}
