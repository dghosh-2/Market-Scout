import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# Get the absolute path to the data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUERIES_FILE = os.path.join(DATA_DIR, "queries.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
REPORT_DATA_FILE = os.path.join(DATA_DIR, "report_data.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_json(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return []


def save_json(filepath: str, data: List[Dict[str, Any]]):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def create_query(request: str, company: str) -> Dict[str, Any]:
    queries = load_json(QUERIES_FILE)
    query = {
        "id": str(uuid.uuid4()),
        "request": request,
        "company": company,
        "created_at": datetime.now().isoformat()
    }
    queries.append(query)
    save_json(QUERIES_FILE, queries)
    return query


def get_queries() -> List[Dict[str, Any]]:
    return load_json(QUERIES_FILE)


def create_report(query_id: str, company: str, report_path: str) -> Dict[str, Any]:
    reports = load_json(REPORTS_FILE)
    
    # Get version number
    company_reports = [r for r in reports if r.get("company", "").lower() == company.lower()]
    version = len(company_reports) + 1
    
    report = {
        "id": str(uuid.uuid4()),
        "query_id": query_id,
        "company": company,
        "report_path": report_path,
        "version": version,
        "created_at": datetime.now().isoformat()
    }
    reports.append(report)
    save_json(REPORTS_FILE, reports)
    return report


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    reports = load_json(REPORTS_FILE)
    for r in reports:
        if r["id"] == report_id:
            return r
    return None


def get_reports_by_company(company: str) -> List[Dict[str, Any]]:
    reports = load_json(REPORTS_FILE)
    return [r for r in reports if company.lower() in r.get("company", "").lower()]


def get_all_reports() -> List[Dict[str, Any]]:
    return load_json(REPORTS_FILE)


def get_grouped_reports() -> Dict[str, List[Dict[str, Any]]]:
    reports = load_json(REPORTS_FILE)
    grouped = {}
    for r in reports:
        company = r.get("company", "Unknown")
        if company not in grouped:
            grouped[company] = []
        grouped[company].append(r)
    return grouped


def create_report_data(report_id: str, company_info: str, financial_data: str, risk_data: str, news_data: str) -> Dict[str, Any]:
    report_data_list = load_json(REPORT_DATA_FILE)
    entry = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "company_info": company_info,
        "financial_data": financial_data,
        "risk_data": risk_data,
        "news_data": news_data,
        "created_at": datetime.now().isoformat()
    }
    report_data_list.append(entry)
    save_json(REPORT_DATA_FILE, report_data_list)
    return entry


def get_report_data(report_id: str) -> Optional[Dict[str, Any]]:
    report_data_list = load_json(REPORT_DATA_FILE)
    for rd in report_data_list:
        if rd["report_id"] == report_id:
            return rd
    return None
