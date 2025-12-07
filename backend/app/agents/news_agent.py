"""
News Agent: Analyzes news, sentiment, and identifies catalysts
"""
import json
from typing import Dict, Any
from app.data.fetch_news import get_comprehensive_news_analysis
from app.utils.llm import call_openai
from app.agents.prompts import get_news_prompt


def gather_news_data(ticker: str) -> Dict[str, Any]:
    """
    Gather news and sentiment data
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with news data
    """
    try:
        # Get comprehensive news analysis
        news_data = get_comprehensive_news_analysis(ticker)
        
        return {
            "news_data": news_data,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def analyze_news_and_sentiment(ticker: str, company_name: str) -> Dict[str, Any]:
    """
    Run news and sentiment analysis using AI
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Gather news data
        data = gather_news_data(ticker)
        
        if not data.get("success"):
            return {
                "error": data.get("error", "Failed to gather news data"),
                "success": False
            }
        
        news_data = data.get("news_data", {})
        
        # Format data for AI
        articles_str = json.dumps(news_data.get("articles", [])[:20], indent=2, default=str)[:8000]
        sentiment_str = json.dumps(news_data.get("sentiment_analysis", {}), indent=2, default=str)
        
        # Get prompt
        system_msg, user_msg = get_news_prompt(
            company_name,
            ticker,
            articles_str,
            sentiment_str
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
            "catalysts": news_data.get("potential_catalysts", []),
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"News analysis failed: {str(e)}",
            "success": False
        }


def get_news_summary(ticker: str, company_name: str) -> str:
    """
    Get formatted news and sentiment summary
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Formatted news summary string
    """
    result = analyze_news_and_sentiment(ticker, company_name)
    
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    return result.get("analysis", "No analysis available")

