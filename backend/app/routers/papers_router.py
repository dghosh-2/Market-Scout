from fastapi import APIRouter, HTTPException
from typing import List
from app.db import file_storage as storage

router = APIRouter()


@router.get("/papers")
async def get_all_papers():
    """Get all reports grouped by company"""
    grouped = storage.get_grouped_reports()
    
    result = []
    for company, reports in grouped.items():
        result.append({
            "company": company,
            "report_count": len(reports),
            "reports": sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)
        })
    
    return sorted(result, key=lambda x: x["reports"][0]["created_at"] if x["reports"] else "", reverse=True)


@router.get("/papers/{company}")
async def get_company_papers(company: str):
    """Get all reports for a specific company"""
    reports = storage.get_reports_by_company(company)
    
    if not reports:
        raise HTTPException(status_code=404, detail=f"No reports found for {company}")
    
    return {
        "company": company,
        "reports": sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)
    }


@router.get("/papers/report/{report_id}")
async def get_paper(report_id: str):
    """Get a specific report by ID"""
    report = storage.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_data = storage.get_report_data(report_id)
    
    return {
        "report": report,
        "data": report_data
    }
