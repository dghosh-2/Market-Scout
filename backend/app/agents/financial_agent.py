"""
Financial Agent: Analyzes financial statements, metrics, and company financial health
"""
import json
from typing import Dict, Any
from app.data.fetch_yfinance import get_financial_data, get_key_metrics
from app.utils.llm import call_openai
from app.agents.prompts import get_financial_prompt


def gather_financial_data(ticker: str) -> Dict[str, Any]:
    """
    Gather financial data from various sources
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with financial data
    """
    try:
        # Get financial statements
        financial_data = get_financial_data(ticker)
        
        # Get key metrics
        key_metrics = get_key_metrics(ticker)
        
        return {
            "financial_data": financial_data,
            "key_metrics": key_metrics,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def analyze_financials(ticker: str, company_name: str) -> Dict[str, Any]:
    """
    Run financial analysis using AI
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Gather financial data
        data = gather_financial_data(ticker)
        
        if not data.get("success"):
            return {
                "error": data.get("error", "Failed to gather financial data"),
                "success": False
            }
        
        # Format data for AI (limit size due to token constraints)
        financial_str = json.dumps(data.get("financial_data", {}), indent=2, default=str)[:10000]
        metrics_str = json.dumps(data.get("key_metrics", {}), indent=2, default=str)
        
        # Get prompt
        system_msg, user_msg = get_financial_prompt(
            company_name, 
            ticker, 
            financial_str, 
            metrics_str
        )
        
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
            "raw_data": data,
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"Financial analysis failed: {str(e)}",
            "success": False
        }


def get_financial_summary(ticker: str, company_name: str) -> str:
    """
    Get formatted financial summary
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Formatted financial summary string
    """
    result = analyze_financials(ticker, company_name)
    
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    return result.get("analysis", "No analysis available")

