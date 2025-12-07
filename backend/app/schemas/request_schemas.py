from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ResearchRequest(BaseModel):
    query: str
    omit_sections: Optional[List[str]] = None
    add_sections: Optional[List[str]] = None


class ResearchResponse(BaseModel):
    success: bool
    message: str
    report_id: Optional[str] = None
    report_path: Optional[str] = None
    company: Optional[str] = None


class FeedbackRequest(BaseModel):
    report_id: str
    feedback: str


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    new_report_id: Optional[str] = None
    new_report_path: Optional[str] = None


class ReportSummary(BaseModel):
    id: str
    company: str
    version: int
    created_at: str
    report_path: str


class CompanyReports(BaseModel):
    company: str
    reports: List[ReportSummary]


class PreviewData(BaseModel):
    ticker: str
    company_name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    change_percent: Optional[float] = None
    logo_url: Optional[str] = None


class ProgressUpdate(BaseModel):
    step: str
    message: str
    data: Optional[Dict[str, Any]] = None
