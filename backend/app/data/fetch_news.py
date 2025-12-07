import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf


def get_yfinance_news(ticker: str, max_items: int = 20) -> List[Dict[str, Any]]:
    """
    Get news articles from yfinance
    
    Args:
        ticker: Stock ticker symbol
        max_items: Maximum number of news items to fetch
        
    Returns:
        List of news articles
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            return []
        
        articles = []
        for item in news[:max_items]:
            article = {
                "title": item.get("title", "No title"),
                "publisher": item.get("publisher", "Unknown"),
                "link": item.get("link", ""),
                "published": datetime.fromtimestamp(item.get("providerPublishTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": item.get("type", "news"),
                "thumbnail": item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "") if item.get("thumbnail") else ""
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        print(f"Error fetching news from yfinance: {str(e)}")
        return []


def search_web_news(query: str, ticker: str) -> List[Dict[str, Any]]:
    """
    Search for news articles about the company
    Note: This is a placeholder. In production, you'd use NewsAPI, Google News API, or web scraping
    
    Args:
        query: Search query
        ticker: Stock ticker symbol
        
    Returns:
        List of news articles
    """
    try:
        # First try yfinance news
        articles = get_yfinance_news(ticker)
        
        if articles:
            return articles
        
        # Placeholder for additional news sources
        # In production, integrate with:
        # - NewsAPI (https://newsapi.org/)
        # - Alpha Vantage News API
        # - Web scraping from financial news sites
        
        return [{
            "title": f"News feed for {ticker}",
            "publisher": "System",
            "link": "",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "system",
            "note": "Using yfinance news feed. Additional news sources can be integrated via NewsAPI or web scraping."
        }]
        
    except Exception as e:
        return [{
            "error": f"Error fetching news: {str(e)}"
        }]


def analyze_news_sentiment(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze sentiment of news articles
    Note: Basic implementation - would use NLP in production
    
    Args:
        articles: List of news articles
        
    Returns:
        Sentiment analysis results
    """
    if not articles:
        return {
            "sentiment": "neutral",
            "score": 0,
            "article_count": 0,
            "note": "No articles to analyze"
        }
    
    # Simple keyword-based sentiment (placeholder)
    # In production, use proper NLP/sentiment analysis tools
    positive_keywords = ["surge", "gain", "profit", "growth", "beat", "upgrade", "bullish", "rally", "success"]
    negative_keywords = ["fall", "loss", "decline", "downgrade", "bearish", "risk", "concern", "lawsuit", "investigation"]
    
    positive_count = 0
    negative_count = 0
    
    for article in articles:
        title = article.get("title", "").lower()
        for keyword in positive_keywords:
            if keyword in title:
                positive_count += 1
        for keyword in negative_keywords:
            if keyword in title:
                negative_count += 1
    
    total = positive_count + negative_count
    if total == 0:
        sentiment = "neutral"
        score = 0
    elif positive_count > negative_count:
        sentiment = "positive"
        score = positive_count / total
    elif negative_count > positive_count:
        sentiment = "negative"
        score = -negative_count / total
    else:
        sentiment = "neutral"
        score = 0
    
    return {
        "sentiment": sentiment,
        "score": round(score, 2),
        "positive_mentions": positive_count,
        "negative_mentions": negative_count,
        "article_count": len(articles),
        "note": "Basic keyword-based sentiment analysis. Use NLP tools for more accurate results."
    }


def identify_catalysts(articles: List[Dict[str, Any]], ticker: str) -> List[str]:
    """
    Identify potential catalysts from news articles
    
    Args:
        articles: List of news articles
        ticker: Stock ticker symbol
        
    Returns:
        List of potential catalysts
    """
    catalyst_keywords = [
        "earnings", "acquisition", "merger", "partnership", "product launch",
        "FDA approval", "contract", "revenue", "guidance", "dividend",
        "buyback", "split", "ipo", "expansion", "innovation"
    ]
    
    catalysts = []
    
    for article in articles:
        title = article.get("title", "").lower()
        for keyword in catalyst_keywords:
            if keyword in title and keyword not in [c.lower() for c in catalysts]:
                catalysts.append(keyword.title())
    
    if not catalysts:
        catalysts.append("No significant catalysts identified in recent news")
    
    return catalysts


def get_comprehensive_news_analysis(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive news analysis including articles, sentiment, and catalysts
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with complete news analysis
    """
    try:
        # Fetch news articles
        articles = get_yfinance_news(ticker)
        
        # Analyze sentiment
        sentiment = analyze_news_sentiment(articles)
        
        # Identify catalysts
        catalysts = identify_catalysts(articles, ticker)
        
        return {
            "ticker": ticker,
            "articles": articles,
            "sentiment_analysis": sentiment,
            "potential_catalysts": catalysts,
            "article_count": len(articles),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "error": f"Error in comprehensive news analysis: {str(e)}"
        }

