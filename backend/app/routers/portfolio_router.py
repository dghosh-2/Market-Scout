from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.db.file_storage import (
    load_json, save_json, DATA_DIR
)
import os
import uuid
from datetime import datetime

router = APIRouter()

PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")


class Holding(BaseModel):
    ticker: str
    shares: float
    company_name: Optional[str] = None


class HoldingUpdate(BaseModel):
    shares: float


class PortfolioResponse(BaseModel):
    holdings: List[dict]
    total_holdings: int


def get_portfolio() -> List[dict]:
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    return load_json(PORTFOLIO_FILE)


def save_portfolio(holdings: List[dict]):
    save_json(PORTFOLIO_FILE, holdings)


@router.get("/portfolio", response_model=PortfolioResponse)
async def list_holdings():
    holdings = get_portfolio()
    return {
        "holdings": holdings,
        "total_holdings": len(holdings)
    }


@router.post("/portfolio")
async def add_holding(holding: Holding):
    holdings = get_portfolio()
    
    existing = next((h for h in holdings if h["ticker"].upper() == holding.ticker.upper()), None)
    if existing:
        raise HTTPException(status_code=400, detail=f"Holding for {holding.ticker} already exists. Use PUT to update.")
    
    new_holding = {
        "id": str(uuid.uuid4()),
        "ticker": holding.ticker.upper(),
        "shares": holding.shares,
        "company_name": holding.company_name or holding.ticker.upper(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    holdings.append(new_holding)
    save_portfolio(holdings)
    
    return {"success": True, "holding": new_holding}


@router.put("/portfolio/{ticker}")
async def update_holding(ticker: str, update: HoldingUpdate):
    holdings = get_portfolio()
    
    holding = next((h for h in holdings if h["ticker"].upper() == ticker.upper()), None)
    if not holding:
        raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")
    
    holding["shares"] = update.shares
    holding["updated_at"] = datetime.now().isoformat()
    
    save_portfolio(holdings)
    
    return {"success": True, "holding": holding}


@router.delete("/portfolio/{ticker}")
async def delete_holding(ticker: str):
    holdings = get_portfolio()
    
    original_count = len(holdings)
    holdings = [h for h in holdings if h["ticker"].upper() != ticker.upper()]
    
    if len(holdings) == original_count:
        raise HTTPException(status_code=404, detail=f"No holding found for {ticker}")
    
    save_portfolio(holdings)
    
    return {"success": True, "message": f"Removed {ticker} from portfolio"}


@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get portfolio summary with current prices"""
    from app.agents.tools import get_financials
    
    holdings = get_portfolio()
    
    if not holdings:
        return {
            "holdings": [],
            "total_value": 0,
            "total_holdings": 0
        }
    
    enriched = []
    total_value = 0
    
    for h in holdings:
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
                "industry": financials.get("industry", "Unknown")
            })
        except:
            enriched.append({
                **h,
                "current_price": 0,
                "value": 0,
                "sector": "Unknown",
                "industry": "Unknown"
            })
    
    for h in enriched:
        h["weight"] = (h["value"] / total_value * 100) if total_value > 0 else 0
    
    return {
        "holdings": enriched,
        "total_value": total_value,
        "total_holdings": len(enriched)
    }


