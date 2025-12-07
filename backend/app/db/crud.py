from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.db.models import Query, Report, ReportData


# ============= Query CRUD =============

def create_query(
    db: Session,
    request: str,
    company: str
) -> Query:
    """Create a new query record"""
    now = datetime.now()
    query = Query(
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        request=request,
        company=company,
        timestamp=now
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


def get_query(db: Session, query_id: int) -> Optional[Query]:
    """Get a query by ID"""
    return db.query(Query).filter(Query.id == query_id).first()


def get_all_queries(db: Session, skip: int = 0, limit: int = 100) -> List[Query]:
    """Get all queries"""
    return db.query(Query).order_by(desc(Query.timestamp)).offset(skip).limit(limit).all()


def get_queries_by_company(db: Session, company: str) -> List[Query]:
    """Get all queries for a specific company"""
    return db.query(Query).filter(Query.company == company).order_by(desc(Query.timestamp)).all()


# ============= Report CRUD =============

def create_report(
    db: Session,
    query_id: int,
    company: str,
    report_path: str
) -> Report:
    """Create a new report record"""
    # Get the latest version number for this company
    latest_report = db.query(Report).filter(Report.company == company).order_by(desc(Report.version)).first()
    version = (latest_report.version + 1) if latest_report else 1
    
    report = Report(
        query_id=query_id,
        company=company,
        report_path=report_path,
        version=version
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: int) -> Optional[Report]:
    """Get a report by ID"""
    return db.query(Report).filter(Report.id == report_id).first()


def get_all_reports(db: Session, skip: int = 0, limit: int = 100) -> List[Report]:
    """Get all reports"""
    return db.query(Report).order_by(desc(Report.created_at)).offset(skip).limit(limit).all()


def get_reports_by_company(db: Session, company: str) -> List[Report]:
    """Get all reports for a specific company"""
    return db.query(Report).filter(Report.company == company).order_by(desc(Report.created_at)).all()


def get_companies_with_reports(db: Session) -> List[str]:
    """Get list of all companies that have reports"""
    results = db.query(Report.company).distinct().all()
    return [r[0] for r in results]


# ============= ReportData CRUD =============

def create_report_data(
    db: Session,
    report_id: int,
    company_info: Optional[str] = None,
    financial_data: Optional[str] = None,
    risk_data: Optional[str] = None,
    news_data: Optional[str] = None
) -> ReportData:
    """Create a new report data record"""
    report_data = ReportData(
        report_id=report_id,
        company_info=company_info,
        financial_data=financial_data,
        risk_data=risk_data,
        news_data=news_data
    )
    db.add(report_data)
    db.commit()
    db.refresh(report_data)
    return report_data


def get_report_data(db: Session, report_id: int) -> Optional[ReportData]:
    """Get report data by report ID"""
    return db.query(ReportData).filter(ReportData.report_id == report_id).first()


def update_report_data(
    db: Session,
    report_id: int,
    company_info: Optional[str] = None,
    financial_data: Optional[str] = None,
    risk_data: Optional[str] = None,
    news_data: Optional[str] = None
) -> Optional[ReportData]:
    """Update report data"""
    report_data = get_report_data(db, report_id)
    if report_data:
        if company_info is not None:
            report_data.company_info = company_info
        if financial_data is not None:
            report_data.financial_data = financial_data
        if risk_data is not None:
            report_data.risk_data = risk_data
        if news_data is not None:
            report_data.news_data = news_data
        db.commit()
        db.refresh(report_data)
    return report_data

