"""
Risk Agent: Identifies and analyzes investment risks
"""
import json
from typing import Dict, Any
from app.data.fetch_yfinance import get_stock_info, get_key_metrics
from app.data.fetch_news import get_yfinance_news
from app.utils.llm import call_openai
from app.agents.prompts import get_risk_prompt


def gather_risk_data(ticker: str) -> Dict[str, Any]:
    """
    Gather data relevant for risk analysis
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with risk-related data
    """
    try:
        # Get company info
        stock_info = get_stock_info(ticker)
        
        # Get financial health metrics
        key_metrics = get_key_metrics(ticker)
        financial_health = key_metrics.get("financial_health", {})
        
        # Get recent news for context
        recent_news = get_yfinance_news(ticker, max_items=10)
        
        return {
            "stock_info": stock_info,
            "financial_health": financial_health,
            "recent_news": recent_news,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def analyze_risks(ticker: str, company_name: str) -> Dict[str, Any]:
    """
    Run risk analysis using AI
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Gather risk data
        data = gather_risk_data(ticker)
        
        if not data.get("success"):
            return {
                "error": data.get("error", "Failed to gather risk data"),
                "success": False
            }
        
        # Format data for AI
        company_info_str = json.dumps(data.get("stock_info", {}), indent=2, default=str)[:5000]
        financial_health_str = json.dumps(data.get("financial_health", {}), indent=2, default=str)
        news_str = json.dumps(data.get("recent_news", [])[:10], indent=2, default=str)[:5000]
        
        # Get prompt
        system_msg, user_msg = get_risk_prompt(
            company_name,
            ticker,
            company_info_str,
            financial_health_str,
            news_str
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
            "error": f"Risk analysis failed: {str(e)}",
            "success": False
        }


def get_risk_assessment(ticker: str, company_name: str) -> str:
    """
    Get formatted risk assessment
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Formatted risk assessment string
    """
    result = analyze_risks(ticker, company_name)
    
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    return result.get("analysis", "No analysis available")

