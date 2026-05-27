"""Parallel node: pulls yfinance risk metrics + computes portfolio-aware volatility."""
from __future__ import annotations

import logging
import math
from typing import Any, Dict

from app.agents.state import ResearchState
from app.agents.tools import aget_risks, get_portfolio_context
from app.telemetry.langfuse_client import observe, update_current_observation

logger = logging.getLogger(__name__)


def _safe_float(value: Any) -> float:
    try:
        if value is None or value == "N/A":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _portfolio_volatility(holdings: list[Dict[str, Any]]) -> float:
    """Rough weighted average of holding-level betas, treating the existing portfolio
    as a single risk proxy. Returns 0 if no usable data."""
    weighted = 0.0
    total_weight = 0.0
    for h in holdings:
        weight = _safe_float(h.get("weight"))
        beta = _safe_float(h.get("beta"))
        if weight <= 0 or beta <= 0:
            continue
        weighted += weight * beta
        total_weight += weight
    if total_weight <= 0:
        return 0.0
    return weighted / total_weight


@observe(name="get_risk_assessment")
async def get_risk_assessment(state: ResearchState) -> Dict[str, Any]:
    ticker = state.get("ticker", "")
    if not ticker:
        return {"errors": ["risk_assessment: missing ticker"], "risk_metrics": {}}

    try:
        risks = await aget_risks(ticker)
    except Exception as e:
        logger.exception("risk_assessment yfinance fetch failed for %s", ticker)
        return {"errors": [f"risk_assessment: {e}"], "risk_metrics": {}}

    portfolio_context = state.get("portfolio_context")
    if portfolio_context is None:
        portfolio_context = await get_portfolio_context()

    holdings = (portfolio_context or {}).get("holdings", [])
    portfolio_beta = _portfolio_volatility(holdings)
    ticker_beta = _safe_float(risks.get("beta"))
    portfolio_after_add = (
        (portfolio_beta + ticker_beta) / 2 if portfolio_beta and ticker_beta else (ticker_beta or portfolio_beta)
    )

    metrics = {
        "ticker": ticker,
        "ticker_beta": ticker_beta,
        "annualized_volatility_percent": _safe_float(risks.get("volatility_percent")),
        "debt_to_equity": risks.get("debt_to_equity"),
        "current_ratio": risks.get("current_ratio"),
        "short_percent_of_float": risks.get("short_percent_of_float"),
        "overall_risk": risks.get("overall_risk"),
        "portfolio_weighted_beta_before": round(portfolio_beta, 4),
        "portfolio_weighted_beta_after_add": round(portfolio_after_add, 4),
        "concentration_risk_pct": _safe_float(
            max((h.get("weight", 0) for h in holdings), default=0)
        ),
        "raw_risks": risks,
    }

    update_current_observation(
        ticker=ticker,
        ticker_beta=ticker_beta,
        portfolio_beta_before=metrics["portfolio_weighted_beta_before"],
        portfolio_beta_after=metrics["portfolio_weighted_beta_after_add"],
        holdings_count=len(holdings),
    )

    return {
        "risk_metrics": metrics,
        "portfolio_context": portfolio_context,
    }
