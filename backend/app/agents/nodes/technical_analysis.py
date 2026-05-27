"""Parallel node: company info + financials + price history from yfinance."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from app.agents.state import ResearchState
from app.agents.tools import aget_company_info, aget_financials, aget_price_history
from app.telemetry.langfuse_client import observe, update_current_observation

logger = logging.getLogger(__name__)


@observe(name="get_technical_analysis")
async def get_technical_analysis(state: ResearchState) -> Dict[str, Any]:
    """Concurrently fetch company info, financials, and 1y price history."""
    ticker = state.get("ticker", "")
    if not ticker:
        return {"errors": ["technical_analysis: missing ticker"], "technical_data": {}}

    try:
        company_info, financials, price_data = await asyncio.gather(
            aget_company_info(ticker),
            aget_financials(ticker),
            aget_price_history(ticker, "1y"),
            return_exceptions=False,
        )
    except Exception as e:
        logger.exception("technical_analysis failed for %s", ticker)
        return {"errors": [f"technical_analysis: {e}"], "technical_data": {}}

    update_current_observation(
        ticker=ticker,
        company_info_keys=len(company_info) if isinstance(company_info, dict) else 0,
        has_financials=bool(financials and "error" not in financials),
        has_price_history=bool(price_data and "error" not in price_data),
    )

    return {
        "technical_data": {
            "company_info": company_info,
            "financials": financials,
        },
        "price_data": price_data,
    }
