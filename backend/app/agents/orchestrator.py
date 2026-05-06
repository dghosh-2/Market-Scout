from typing import Dict, Any, List, Optional
from app.utils.validation import resolve_company_to_ticker, parse_user_query
from app.agents.master_agent import run_master_agent
from app.agents.tools import get_price_history


def orchestrate_research(
    query: str,
    omit_sections: Optional[List[str]] = None,
    add_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Main orchestration function for research pipeline"""
    
    # Parse the user query
    parsed = parse_user_query(query)
    company_query = parsed["company_query"]
    custom_request = parsed["custom_request"]
    parsed_omissions = parsed.get("omissions") or []
    parsed_add = parsed.get("add_sections") or []

    merged_omit: List[str] = []
    for x in list(omit_sections or []) + list(parsed_omissions):
        if x and str(x).lower() not in merged_omit:
            merged_omit.append(str(x).lower())

    merged_add: List[str] = []
    for x in list(add_sections or []) + list(parsed_add):
        if x and str(x) not in merged_add:
            merged_add.append(str(x))
    
    # Resolve ticker
    ticker, company_name, error = resolve_company_to_ticker(company_query)
    
    if error:
        return {
            "success": False,
            "error": error
        }
    
    # Run master agent
    result = run_master_agent(
        ticker=ticker,
        company_name=company_name,
        user_query=query,
        custom_request=custom_request,
        omit_sections=merged_omit,
        add_sections=merged_add,
    )
    
    # Get price history for charts
    price_data = get_price_history(ticker, "1y")
    result["price_data"] = price_data
    
    return {
        "success": True,
        "data": result
    }
