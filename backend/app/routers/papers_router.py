from fastapi import APIRouter, HTTPException
from app.db import smoldb

router = APIRouter()


def _norm_report(r: dict) -> dict:
    return {str(k).lower(): v for k, v in r.items()}


@router.get("/papers")
async def get_all_papers():
    """Get all reports grouped by company"""
    smoldb.ensure_schema()
    grouped = smoldb.get_grouped_reports()

    result = []
    for company, reports in grouped.items():
        norm_reports = [_norm_report(x) for x in reports]
        result.append({
            "company": company,
            "report_count": len(norm_reports),
            "reports": sorted(
                norm_reports,
                key=lambda x: x.get("created_at", "") or "",
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
    """Get all reports for a specific company (ticker exact match preferred)."""
    smoldb.ensure_schema()
    reports = smoldb.get_reports_for_identifier(company)

    if not reports:
        raise HTTPException(status_code=404, detail=f"No reports found for {company}")

    norm_reports = [_norm_report(x) for x in reports]
    return {
        "company": company,
        "reports": sorted(
            norm_reports,
            key=lambda x: x.get("created_at", "") or "",
            reverse=True,
        ),
    }


@router.get("/papers/report/{report_id}")
async def get_paper(report_id: str):
    """Get a specific report by ID"""
    smoldb.ensure_schema()
    report = smoldb.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data = smoldb.get_report_data(report_id)

    return {
        "report": _norm_report(report),
        "data": {str(k).lower(): v for k, v in (report_data or {}).items()},
    }
