import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import yfinance as yf


def get_company_info(ticker: str) -> Dict[str, Any]:
    """Get company overview, business description, and basic info"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "ticker": ticker,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "description": info.get("longBusinessSummary", ""),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees", ""),
            "country": info.get("country", ""),
            "city": info.get("city", ""),
            "market_cap": info.get("marketCap", 0),
            "enterprise_value": info.get("enterpriseValue", 0),
            "logo_url": info.get("logo_url", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def get_financials(ticker: str) -> Dict[str, Any]:
    """Get financial data, metrics, and valuation"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "ticker": ticker,
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "previous_close": info.get("previousClose", 0),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "peg_ratio": info.get("pegRatio", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),
            "dividend_yield": info.get("dividendYield", 0),
            "profit_margins": info.get("profitMargins", "N/A"),
            "operating_margins": info.get("operatingMargins", "N/A"),
            "gross_margins": info.get("grossMargins", "N/A"),
            "revenue": info.get("totalRevenue", 0),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "earnings_growth": info.get("earningsGrowth", "N/A"),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "return_on_assets": info.get("returnOnAssets", "N/A"),
            "total_cash": info.get("totalCash", 0),
            "total_debt": info.get("totalDebt", 0),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "free_cash_flow": info.get("freeCashflow", 0),
            "earnings_per_share": info.get("trailingEps", "N/A"),
            "analyst_target_price": info.get("targetMeanPrice", "N/A"),
            "analyst_recommendation": info.get("recommendationKey", "N/A"),
            "number_of_analysts": info.get("numberOfAnalystOpinions", 0),
        }
    except Exception as e:
        return {"error": str(e)}


def get_risks(ticker: str) -> Dict[str, Any]:
    """Get risk-related data and metrics"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        beta = info.get("beta", "N/A")
        
        hist = stock.history(period="3mo")
        volatility = "N/A"
        if not hist.empty and len(hist) > 1:
            returns = hist['Close'].pct_change().dropna()
            if len(returns) > 0:
                volatility = round(returns.std() * (252 ** 0.5) * 100, 2)
        
        return {
            "ticker": ticker,
            "beta": beta,
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "volatility_percent": volatility,
            "short_percent_of_float": info.get("shortPercentOfFloat", "N/A"),
            "held_percent_insiders": info.get("heldPercentInsiders", "N/A"),
            "held_percent_institutions": info.get("heldPercentInstitutions", "N/A"),
            "audit_risk": info.get("auditRisk", "N/A"),
            "board_risk": info.get("boardRisk", "N/A"),
            "compensation_risk": info.get("compensationRisk", "N/A"),
            "shareholder_rights_risk": info.get("shareHolderRightsRisk", "N/A"),
            "overall_risk": info.get("overallRisk", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_news(ticker: str) -> Dict[str, Any]:
    """Get recent news and sentiment indicators"""
    try:
        stock = yf.Ticker(ticker)
        news_data = stock.news or []
        
        articles = []
        for item in news_data[:10]:
            # Handle both old and new yfinance news formats
            title = ""
            publisher = ""
            link = ""
            published = ""
            
            # New format: news is a list of dicts with 'content' key
            if isinstance(item, dict):
                # Try new format first (content nested structure)
                if "content" in item:
                    content = item.get("content", {})
                    title = content.get("title", "") or item.get("title", "")
                    publisher = content.get("provider", {}).get("displayName", "") if isinstance(content.get("provider"), dict) else ""
                    link = content.get("canonicalUrl", {}).get("url", "") if isinstance(content.get("canonicalUrl"), dict) else ""
                    pub_time = content.get("pubDate", "")
                    if pub_time:
                        try:
                            published = pub_time[:16].replace("T", " ")
                        except:
                            published = ""
                else:
                    # Old format
                    title = item.get("title", "")
                    publisher = item.get("publisher", "")
                    link = item.get("link", "")
                    pub_time = item.get("providerPublishTime", 0)
                    if pub_time and isinstance(pub_time, (int, float)):
                        try:
                            published = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M")
                        except:
                            published = ""
            
            if title:
                articles.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "published": published,
                })
        
        positive_words = ["surge", "gain", "profit", "growth", "beat", "upgrade", "bullish", "rally", "success", "soar", "jump", "rise", "strong", "record", "high", "boost"]
        negative_words = ["fall", "loss", "decline", "downgrade", "bearish", "risk", "concern", "lawsuit", "investigation", "drop", "plunge", "crash", "weak", "miss", "cut", "low", "warning"]
        
        pos_count = neg_count = 0
        for article in articles:
            title_lower = article["title"].lower()
            for word in positive_words:
                if word in title_lower:
                    pos_count += 1
            for word in negative_words:
                if word in title_lower:
                    neg_count += 1
        
        sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"
        
        return {
            "ticker": ticker,
            "articles": articles,
            "article_count": len(articles),
            "sentiment": sentiment,
            "positive_signals": pos_count,
            "negative_signals": neg_count,
        }
    except Exception as e:
        return {"error": str(e), "articles": [], "article_count": 0}


def get_price_history(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """Get historical price data for charts"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {"error": "No historical data available"}
        
        prices = []
        for date, row in hist.iterrows():
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
        
        return {
            "ticker": ticker,
            "period": period,
            "prices": prices,
            "start_date": prices[0]["date"] if prices else "",
            "end_date": prices[-1]["date"] if prices else "",
            "start_price": prices[0]["close"] if prices else 0,
            "end_price": prices[-1]["close"] if prices else 0,
            "change_percent": round(((prices[-1]["close"] - prices[0]["close"]) / prices[0]["close"]) * 100, 2) if prices else 0,
        }
    except Exception as e:
        return {"error": str(e)}


def get_other(ticker: str, custom_request: str) -> Dict[str, Any]:
    """Get additional data based on custom user request"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        data = {
            "ticker": ticker,
            "custom_request": custom_request,
            "additional_data": {}
        }
        
        request_lower = custom_request.lower()
        
        if any(word in request_lower for word in ["dividend", "yield", "income"]):
            data["additional_data"]["dividends"] = {
                "dividend_rate": info.get("dividendRate", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "payout_ratio": info.get("payoutRatio", "N/A"),
                "ex_dividend_date": info.get("exDividendDate", "N/A"),
            }
        
        if any(word in request_lower for word in ["growth", "expand", "future"]):
            data["additional_data"]["growth"] = {
                "revenue_growth": info.get("revenueGrowth", "N/A"),
                "earnings_growth": info.get("earningsGrowth", "N/A"),
                "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth", "N/A"),
            }
        
        if any(word in request_lower for word in ["insider", "institution", "ownership"]):
            data["additional_data"]["ownership"] = {
                "insiders_percent": info.get("heldPercentInsiders", "N/A"),
                "institutions_percent": info.get("heldPercentInstitutions", "N/A"),
                "float_shares": info.get("floatShares", "N/A"),
            }
        
        if not data["additional_data"]:
            data["additional_data"]["general"] = {
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else "",
            }
        
        return data
    except Exception as e:
        return {"error": str(e)}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "Get company overview including business description, sector, industry, and basic information",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_financials",
            "description": "Get financial data including revenue, earnings, margins, valuation metrics",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_risks",
            "description": "Get risk-related data including beta, volatility, debt levels",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get recent news articles and sentiment analysis",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Get historical price data for charts",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string"}}, "required": ["ticker"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_other",
            "description": "Get additional custom data",
            "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}, "custom_request": {"type": "string"}}, "required": ["ticker", "custom_request"]}
        }
    }
]


async def get_portfolio_context() -> Dict[str, Any]:
    """Async portfolio context using the Postgres repository.
    Fetches yfinance financials concurrently per holding via to_thread."""
    from app.db.database import session_scope
    from app.db.repositories import portfolio as portfolio_repo

    try:
        async with session_scope() as session:
            holdings = await portfolio_repo.list_all(session)
    except Exception:
        return {"holdings": [], "total_value": 0, "sectors": {}}

    if not holdings:
        return {"holdings": [], "total_value": 0, "sectors": {}}

    fin_results = await asyncio.gather(
        *(asyncio.to_thread(get_financials, h["ticker"]) for h in holdings),
        return_exceptions=True,
    )

    enriched: List[Dict[str, Any]] = []
    sectors: Dict[str, Dict[str, Any]] = {}
    total_value = 0.0

    for h, fin in zip(holdings, fin_results):
        if isinstance(fin, Exception) or not isinstance(fin, dict):
            enriched.append({
                "ticker": h["ticker"],
                "shares": h["shares"],
                "company_name": h.get("company_name", h["ticker"]),
                "current_price": 0,
                "value": 0,
                "sector": "Unknown",
            })
            continue

        current_price = fin.get("current_price") or 0
        value = float(current_price) * float(h["shares"])
        total_value += value
        sector = fin.get("sector", "Unknown") or "Unknown"
        bucket = sectors.setdefault(sector, {"value": 0.0, "tickers": []})
        bucket["value"] += value
        bucket["tickers"].append(h["ticker"])

        enriched.append({
            "ticker": h["ticker"],
            "shares": h["shares"],
            "company_name": h.get("company_name", h["ticker"]),
            "current_price": current_price,
            "value": value,
            "sector": sector,
            "pe_ratio": fin.get("pe_ratio"),
            "dividend_yield": fin.get("dividend_yield"),
            "beta": fin.get("beta"),
        })

    for h in enriched:
        h["weight"] = (h["value"] / total_value * 100) if total_value > 0 else 0
    for sector in sectors.values():
        sector["weight"] = (sector["value"] / total_value * 100) if total_value > 0 else 0

    return {
        "holdings": enriched,
        "total_value": total_value,
        "total_holdings": len(enriched),
        "sectors": sectors,
    }


# --- Async wrappers — yfinance is blocking, run via to_thread ---


async def aget_company_info(ticker: str) -> Dict[str, Any]:
    return await asyncio.to_thread(get_company_info, ticker)


async def aget_financials(ticker: str) -> Dict[str, Any]:
    return await asyncio.to_thread(get_financials, ticker)


async def aget_risks(ticker: str) -> Dict[str, Any]:
    return await asyncio.to_thread(get_risks, ticker)


async def aget_news(ticker: str) -> Dict[str, Any]:
    return await asyncio.to_thread(get_news, ticker)


async def aget_price_history(ticker: str, period: str = "1y") -> Dict[str, Any]:
    return await asyncio.to_thread(get_price_history, ticker, period)


async def aget_other(ticker: str, custom_request: str) -> Dict[str, Any]:
    return await asyncio.to_thread(get_other, ticker, custom_request)


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name (sync; portfolio_context is async-only now)."""
    tools = {
        "get_company_info": get_company_info,
        "get_financials": get_financials,
        "get_risks": get_risks,
        "get_news": get_news,
        "get_price_history": get_price_history,
        "get_other": get_other,
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
