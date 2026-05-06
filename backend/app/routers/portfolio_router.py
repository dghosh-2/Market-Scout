from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.db import smoldb
import uuid
from datetime import datetime

router = APIRouter()


class Holding(BaseModel):
    ticker: str
    shares: float
    company_name: Optional[str] = None


class HoldingUpdate(BaseModel):
    shares: float


class PortfolioResponse(BaseModel):
    holdings: List[dict]
    total_holdings: int


def _normalize_row(row: dict) -> dict:
    return {str(k).lower(): v for k, v in row.items()}


def _row_to_api_holding(r: dict) -> dict:
    n = _normalize_row(r)
    return {
        "id": n.get("holding_id") or n.get("ticker"),
        "ticker": n.get("ticker", ""),
        "shares": float(n.get("shares") or 0),
        "company_name": n.get("company_name") or n.get("ticker", ""),
        "created_at": n.get("created_at") or "",
        "updated_at": n.get("updated_at") or "",
    }


@router.get("/portfolio", response_model=PortfolioResponse)
async def list_holdings():
    smoldb.ensure_schema()
    rows = smoldb.portfolio_list_all()
    holdings = [_row_to_api_holding(r) for r in rows]
    return {
        "holdings": holdings,
        "total_holdings": len(holdings),
    }


@router.post("/portfolio")
async def add_holding(holding: Holding):
    smoldb.ensure_schema()
    rows = smoldb.portfolio_list_all()
    tick = holding.ticker.upper()
    for r in rows:
        if _normalize_row(r).get("ticker", "").upper() == tick:
            raise HTTPException(
                status_code=400,
                detail=f"Holding for {holding.ticker} already exists. Use PUT to update.",
            )

    now = datetime.utcnow().isoformat()
    hid = str(uuid.uuid4())
    smoldb.portfolio_upsert_insert(
        ticker=tick,
        shares=float(holding.shares),
        company_name=holding.company_name or tick,
        holding_id=hid,
        created_at=now,
        updated_at=now,
        purchase_price=None,
    )

    new_holding = {
        "id": hid,
        "ticker": tick,
        "shares": float(holding.shares),
        "company_name": holding.company_name or tick,
        "created_at": now,
        "updated_at": now,
    }
    return {"success": True, "holding": new_holding}


@router.put("/portfolio/{ticker}")
async def update_holding(ticker: str, update: HoldingUpdate):
    smoldb.ensure_schema()
    row = smoldb.portfolio_get(ticker)
    if not row:
        raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")

    now = datetime.utcnow().isoformat()
    smoldb.portfolio_update_shares(ticker, float(update.shares), now)
    row2 = smoldb.portfolio_get(ticker)
    return {"success": True, "holding": _row_to_api_holding(row2 or {})}


@router.delete("/portfolio/{ticker}")
async def delete_holding(ticker: str):
    smoldb.ensure_schema()
    row = smoldb.portfolio_get(ticker)
    if not row:
        raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")
    smoldb.portfolio_delete(ticker)
    return {"success": True, "message": f"Removed {ticker} from portfolio"}


@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get portfolio summary with current prices"""
    from app.agents.tools import get_financials

    smoldb.ensure_schema()
    rows = smoldb.portfolio_list_all()

    if not rows:
        return {
            "holdings": [],
            "total_value": 0,
            "total_holdings": 0,
        }

    enriched = []
    total_value = 0

    for r in rows:
        h = _row_to_api_holding(r)
        try:
            financials = get_financials(h["ticker"])
            current_price = financials.get("current_price", 0) or 0
            value = current_price * h["shares"]
            total_value += value

            enriched.append({
                **h,
                "current_price": current_price,
                "value": value,
                "sector": financials.get("sector", "Unknown"),
                "industry": financials.get("industry", "Unknown"),
            })
        except Exception:
            enriched.append({
                **h,
                "current_price": 0,
                "value": 0,
                "sector": "Unknown",
                "industry": "Unknown",
            })

    for h in enriched:
        h["weight"] = (h["value"] / total_value * 100) if total_value > 0 else 0

    return {
        "holdings": enriched,
        "total_value": total_value,
        "total_holdings": len(enriched),
    }
