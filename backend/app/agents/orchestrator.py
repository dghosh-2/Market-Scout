from typing import Dict, Any
from app.utils.validation import resolve_company_to_ticker, parse_user_query
from app.agents.master_agent import run_master_agent
from app.agents.tools import get_price_history


def orchestrate_research(query: str) -> Dict[str, Any]:
    """Main orchestration function for research pipeline"""
    
    # Parse the user query
    parsed = parse_user_query(query)
    company_query = parsed["company_query"]
    custom_request = parsed["custom_request"]
    
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
        custom_request=custom_request
    )
    
    # Get price history for charts
    price_data = get_price_history(ticker, "1y")
    result["price_data"] = price_data
    
    return {
        "success": True,
        "data": result
    }
