import asyncio
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.tools import aget_financials
from app.db.database import session_scope
from app.db.repositories import portfolio as portfolio_repo

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


def _api_holding(h: dict) -> dict:
    return {
        "id": h.get("holding_id") or h.get("ticker"),
        "ticker": h.get("ticker", ""),
        "shares": float(h.get("shares") or 0),
        "company_name": h.get("company_name") or h.get("ticker", ""),
        "created_at": h.get("created_at") or "",
        "updated_at": h.get("updated_at") or "",
    }


@router.get("/portfolio", response_model=PortfolioResponse)
async def list_holdings():
    async with session_scope() as session:
        rows = await portfolio_repo.list_all(session)
    holdings = [_api_holding(r) for r in rows]
    return {"holdings": holdings, "total_holdings": len(holdings)}


@router.post("/portfolio")
async def add_holding(holding: Holding):
    tick = holding.ticker.upper()
    async with session_scope() as session:
        existing = await portfolio_repo.get(session, tick)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Holding for {holding.ticker} already exists. Use PUT to update.",
            )
        new_row = await portfolio_repo.insert(
            session,
            ticker=tick,
            shares=float(holding.shares),
            company_name=holding.company_name or tick,
            holding_id=str(uuid.uuid4()),
        )
    return {"success": True, "holding": _api_holding(new_row)}


@router.put("/portfolio/{ticker}")
async def update_holding(ticker: str, update: HoldingUpdate):
    async with session_scope() as session:
        updated = await portfolio_repo.update_shares(
            session, ticker=ticker, shares=float(update.shares)
        )
        if updated is None:
            raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")
    return {"success": True, "holding": _api_holding(updated)}


@router.delete("/portfolio/{ticker}")
async def delete_holding(ticker: str):
    async with session_scope() as session:
        ok = await portfolio_repo.delete(session, ticker)
        if not ok:
            raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")
    return {"success": True, "message": f"Removed {ticker} from portfolio"}


@router.get("/portfolio/summary")
async def get_portfolio_summary():
    async with session_scope() as session:
        rows = await portfolio_repo.list_all(session)

    if not rows:
        return {"holdings": [], "total_value": 0, "total_holdings": 0}

    fin_results = await asyncio.gather(
        *(aget_financials(r["ticker"]) for r in rows),
        return_exceptions=True,
    )

    enriched = []
    total_value = 0.0
    for r, fin in zip(rows, fin_results):
        base = _api_holding(r)
        if isinstance(fin, Exception) or not isinstance(fin, dict):
            enriched.append({
                **base,
                "current_price": 0,
                "value": 0,
                "sector": "Unknown",
                "industry": "Unknown",
            })
            continue
        current_price = fin.get("current_price") or 0
        value = float(current_price) * base["shares"]
        total_value += value
        enriched.append({
            **base,
            "current_price": current_price,
            "value": value,
            "sector": fin.get("sector", "Unknown"),
            "industry": fin.get("industry", "Unknown"),
        })

    for h in enriched:
        h["weight"] = (h["value"] / total_value * 100) if total_value > 0 else 0

    return {
        "holdings": enriched,
        "total_value": total_value,
        "total_holdings": len(enriched),
    }
