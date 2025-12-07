"""
Company Agent: Analyzes company information, competitors, and market position
"""
import json
from typing import Dict, Any
from app.data.fetch_yfinance import get_stock_info, get_competitors
from app.utils.llm import call_openai
from app.agents.prompts import get_company_prompt


def gather_company_data(ticker: str) -> Dict[str, Any]:
    """
    Gather company data from various sources
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with company data
    """
    try:
        # Get stock info from yfinance
        stock_info = get_stock_info(ticker)
        
        # Get competitor info
        competitor_info = get_competitors(ticker)
        
        return {
            "stock_info": stock_info,
            "competitor_info": competitor_info,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def analyze_company(ticker: str, company_name: str) -> Dict[str, Any]:
    """
    Run company analysis using AI
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Gather company data
        company_data = gather_company_data(ticker)
        
        if not company_data.get("success"):
            return {
                "error": company_data.get("error", "Failed to gather company data"),
                "success": False
            }
        
        # Format data for AI
        data_str = json.dumps(company_data, indent=2, default=str)
        
        # Get prompt
        system_msg, user_msg = get_company_prompt(company_name, ticker, data_str)
        
        # Call AI
        analysis = call_openai(
            prompt=user_msg,
            system_message=system_msg,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000
        )
        
        return {
            "analysis": analysis,
            "raw_data": company_data,
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"Company analysis failed: {str(e)}",
            "success": False
        }


def get_company_overview(ticker: str, company_name: str) -> str:
    """
    Get formatted company overview
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Formatted company overview string
    """
    result = analyze_company(ticker, company_name)
    
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    return result.get("analysis", "No analysis available")

