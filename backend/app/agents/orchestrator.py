"""Async orchestration: parse + resolve + run LangGraph DAG."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.agents.graph import run_research_graph
from app.agents.state import ResearchState
from app.telemetry.langfuse_client import observe
from app.utils.validation import parse_user_query, resolve_company_to_ticker


@observe(name="orchestrate_research")
async def orchestrate_research(
    query: str,
    omit_sections: Optional[List[str]] = None,
    add_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    parsed = await asyncio.to_thread(parse_user_query, query)
    company_query = parsed["company_query"]
    custom_request = parsed["custom_request"]
    parsed_omissions = parsed.get("omissions") or []
    parsed_add = parsed.get("add_sections") or []

    merged_omit: List[str] = []
    for x in list(omit_sections or []) + list(parsed_omissions):
        s = str(x).lower() if x else ""
        if s and s not in merged_omit:
            merged_omit.append(s)

    merged_add: List[str] = []
    for x in list(add_sections or []) + list(parsed_add):
        s = str(x) if x else ""
        if s and s not in merged_add:
            merged_add.append(s)

    ticker, company_name, error = await asyncio.to_thread(
        resolve_company_to_ticker, company_query
    )
    if error:
        return {"success": False, "error": error}

    initial_state: ResearchState = {
        "user_query": query,
        "ticker": ticker,
        "company_name": company_name,
        "custom_request": custom_request,
        "omit_sections": merged_omit,
        "add_sections": merged_add,
    }

    final_state = await run_research_graph(initial_state)

    final_report = final_state.get("final_report")
    if not final_report:
        errors = final_state.get("errors") or ["Graph produced no final report"]
        return {"success": False, "error": "; ".join(errors)}

    return {"success": True, "data": final_report}
