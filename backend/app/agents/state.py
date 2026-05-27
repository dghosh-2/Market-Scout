"""Shared state for the LangGraph research DAG."""
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ResearchState(TypedDict, total=False):
    # Inputs
    user_query: str
    ticker: str
    company_name: str
    custom_request: str
    omit_sections: List[str]
    add_sections: List[str]

    # Pulled by individual nodes
    portfolio_context: Dict[str, Any]
    technical_data: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    news_data: Dict[str, Any]
    news_summary: str
    news_reflections: List[Dict[str, Any]]
    price_data: Dict[str, Any]

    # Compiled output
    analysis_sections: Dict[str, str]
    final_report: Dict[str, Any]

    # Telemetry
    token_usage: Dict[str, int]
    cache_hit: bool

    # Errors from individual nodes accumulate here so we can fail soft
    errors: Annotated[List[str], operator.add]
