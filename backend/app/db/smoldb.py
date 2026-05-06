"""
HTTP client for smoldb (https://smoldb.fly.dev).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_SCHEMA_INITIALIZED = False


def _sql_literal(value: Optional[str]) -> str:
    if value is None:
        return "NULL"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _query_url() -> str:
    settings = get_settings()
    base = settings.smoldb_url.rstrip("/")
    return f"{base}/query"


def execute_sql(sql: str) -> Dict[str, Any]:
    """Run arbitrary SQL against smoldb. Returns parsed JSON body."""
    settings = get_settings()
    if not settings.smoldb_key:
        raise RuntimeError("SMOLDB_KEY is not configured")

    resp = requests.post(
        _query_url(),
        headers={
            "x-api-key": settings.smoldb_key,
            "Content-Type": "application/json",
        },
        json={"sql": sql},
        timeout=60,
    )
    if not resp.ok:
        logger.error("smoldb error %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


def fetch_all(sql: str) -> List[Dict[str, Any]]:
    body = execute_sql(sql)
    rows = body.get("rows")
    if rows is None:
        return []
    return rows


def fetch_one(sql: str) -> Optional[Dict[str, Any]]:
    rows = fetch_all(sql)
    return rows[0] if rows else None


def init_schema() -> None:
    """Create tables if they do not exist (idempotent)."""
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED:
        return

    statements = [
        """
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT PRIMARY KEY,
            request TEXT NOT NULL,
            company TEXT NOT NULL,
            ticker TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            query_id TEXT NOT NULL,
            company TEXT NOT NULL,
            ticker TEXT NOT NULL,
            report_path TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (query_id) REFERENCES queries(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS report_data (
            report_id TEXT PRIMARY KEY,
            company_info TEXT,
            financial_data TEXT,
            risk_data TEXT,
            news_data TEXT,
            analysis TEXT,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS portfolio (
            ticker TEXT PRIMARY KEY,
            shares REAL NOT NULL,
            purchase_price REAL,
            company_name TEXT,
            holding_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_reports_ticker ON reports(ticker)",
        "CREATE INDEX IF NOT EXISTS idx_reports_company ON reports(company)",
    ]

    for stmt in statements:
        execute_sql(stmt.strip())

    _SCHEMA_INITIALIZED = True


def ensure_schema() -> None:
    try:
        init_schema()
    except Exception as e:
        logger.warning("smoldb schema init deferred or failed: %s", e)


# --- Queries / reports (replaces file_storage) ---


def create_query(request: str, company: str, ticker: str) -> Dict[str, Any]:
    import uuid
    from datetime import datetime

    qid = str(uuid.uuid4())
    sql = f"""
    INSERT INTO queries (id, request, company, ticker)
    VALUES ({_sql_literal(qid)}, {_sql_literal(request)}, {_sql_literal(company)}, {_sql_literal(ticker)})
    """
    execute_sql(sql)
    return {
        "id": qid,
        "request": request,
        "company": company,
        "ticker": ticker.upper(),
        "created_at": datetime.utcnow().isoformat(),
    }


def _next_version_for_ticker(ticker: str) -> int:
    row = fetch_one(
        f"SELECT COUNT(*) AS c FROM reports WHERE ticker = {_sql_literal(ticker.upper())}"
    )
    if not row:
        return 1
    c = row.get("c") or row.get("C") or 0
    try:
        return int(c) + 1
    except (TypeError, ValueError):
        return 1


def create_report(query_id: str, company: str, ticker: str, report_path: str) -> Dict[str, Any]:
    import uuid
    from datetime import datetime

    rid = str(uuid.uuid4())
    version = _next_version_for_ticker(ticker)
    sql = f"""
    INSERT INTO reports (id, query_id, company, ticker, report_path, version)
    VALUES (
        {_sql_literal(rid)},
        {_sql_literal(query_id)},
        {_sql_literal(company)},
        {_sql_literal(ticker.upper())},
        {_sql_literal(report_path)},
        {int(version)}
    )
    """
    execute_sql(sql)
    return {
        "id": rid,
        "query_id": query_id,
        "company": company,
        "ticker": ticker.upper(),
        "report_path": report_path,
        "version": version,
        "created_at": datetime.utcnow().isoformat(),
    }


def update_report_path(report_id: str, report_path: str) -> None:
    execute_sql(
        f"UPDATE reports SET report_path = {_sql_literal(report_path)} WHERE id = {_sql_literal(report_id)}"
    )


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one(f"SELECT * FROM reports WHERE id = {_sql_literal(report_id)}")


def get_reports_by_ticker(ticker: str) -> List[Dict[str, Any]]:
    return fetch_all(
        f"SELECT * FROM reports WHERE ticker = {_sql_literal(ticker.upper())} ORDER BY created_at DESC"
    )


def get_reports_by_company_substring(company: str) -> List[Dict[str, Any]]:
    """Fallback: substring match on company display string (case-insensitive)."""
    needle = company.strip().lower().replace("%", "")
    if not needle:
        return []
    like = f"%{needle}%"
    return fetch_all(
        f"SELECT * FROM reports WHERE LOWER(company) LIKE LOWER({_sql_literal(like)}) ORDER BY created_at DESC"
    )


def get_reports_for_identifier(company_or_ticker: str) -> List[Dict[str, Any]]:
    ticker = company_or_ticker.strip().upper()
    by_ticker = get_reports_by_ticker(ticker)
    if by_ticker:
        return by_ticker
    return get_reports_by_company_substring(company_or_ticker)


def get_all_reports() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM reports ORDER BY created_at DESC")


def get_grouped_reports() -> Dict[str, List[Dict[str, Any]]]:
    reports = get_all_reports()
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in reports:
        company = r.get("company") or "Unknown"
        grouped.setdefault(company, []).append(r)
    return grouped


def create_report_data(
    report_id: str,
    company_info: str,
    financial_data: str,
    risk_data: str,
    news_data: str,
    analysis: Optional[str] = None,
) -> Dict[str, Any]:
    sql = f"""
    INSERT INTO report_data (report_id, company_info, financial_data, risk_data, news_data, analysis)
    VALUES (
        {_sql_literal(report_id)},
        {_sql_literal(company_info)},
        {_sql_literal(financial_data)},
        {_sql_literal(risk_data)},
        {_sql_literal(news_data)},
        {_sql_literal(analysis)}
    )
    """
    execute_sql(sql)
    return {"report_id": report_id}


def get_report_data(report_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one(
        f"SELECT * FROM report_data WHERE report_id = {_sql_literal(report_id)}"
    )


# --- Portfolio ---


def portfolio_list_all() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM portfolio ORDER BY ticker ASC")


def portfolio_get(ticker: str) -> Optional[Dict[str, Any]]:
    return fetch_one(
        f"SELECT * FROM portfolio WHERE ticker = {_sql_literal(ticker.upper())}"
    )


def portfolio_upsert_insert(
    ticker: str,
    shares: float,
    company_name: Optional[str],
    holding_id: str,
    created_at: str,
    updated_at: str,
    purchase_price: Optional[float] = None,
) -> None:
    cn = _sql_literal(company_name or ticker.upper())
    pp = "NULL" if purchase_price is None else str(float(purchase_price))
    sql = f"""
    INSERT INTO portfolio (ticker, shares, purchase_price, company_name, holding_id, created_at, updated_at)
    VALUES (
        {_sql_literal(ticker.upper())},
        {float(shares)},
        {pp},
        {cn},
        {_sql_literal(holding_id)},
        {_sql_literal(created_at)},
        {_sql_literal(updated_at)}
    )
    """
    execute_sql(sql)


def portfolio_update_shares(ticker: str, shares: float, updated_at: str) -> None:
    execute_sql(
        f"UPDATE portfolio SET shares = {float(shares)}, updated_at = {_sql_literal(updated_at)} "
        f"WHERE ticker = {_sql_literal(ticker.upper())}"
    )


def portfolio_delete(ticker: str) -> None:
    execute_sql(f"DELETE FROM portfolio WHERE ticker = {_sql_literal(ticker.upper())}")


def extract_ticker_from_company_label(company: str) -> str:
    if "(" in company and ")" in company:
        return company.split("(")[-1].replace(")", "").strip().upper()
    return company.strip().upper()
