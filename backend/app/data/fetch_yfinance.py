import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive stock information from yfinance
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with stock information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key information
        stock_data = {
            "symbol": ticker,
            "company_name": info.get("longName", "Unknown"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "previous_close": info.get("previousClose", 0),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": info.get("dividendYield", 0),
            "beta": info.get("beta", "N/A"),
            "description": info.get("longBusinessSummary", "No description available"),
            "website": info.get("website", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "country": info.get("country", "N/A"),
            "city": info.get("city", "N/A")
        }
        
        return stock_data
    except Exception as e:
        raise Exception(f"Error fetching stock info for {ticker}: {str(e)}")


def get_financial_data(ticker: str) -> Dict[str, Any]:
    """
    Get financial statements (income statement, balance sheet, cash flow)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with financial data
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        financials = stock.financials  # Annual income statement
        quarterly_financials = stock.quarterly_financials  # Quarterly income statement
        balance_sheet = stock.balance_sheet  # Annual balance sheet
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        cash_flow = stock.cashflow  # Annual cash flow
        quarterly_cash_flow = stock.quarterly_cashflow
        
        financial_data = {
            "annual_financials": financials.to_dict() if not financials.empty else {},
            "quarterly_financials": quarterly_financials.to_dict() if not quarterly_financials.empty else {},
            "balance_sheet": balance_sheet.to_dict() if not balance_sheet.empty else {},
            "quarterly_balance_sheet": quarterly_balance_sheet.to_dict() if not quarterly_balance_sheet.empty else {},
            "cash_flow": cash_flow.to_dict() if not cash_flow.empty else {},
            "quarterly_cash_flow": quarterly_cash_flow.to_dict() if not quarterly_cash_flow.empty else {}
        }
        
        return financial_data
    except Exception as e:
        raise Exception(f"Error fetching financial data for {ticker}: {str(e)}")


def get_key_metrics(ticker: str) -> Dict[str, Any]:
    """
    Get key financial metrics and ratios
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with key metrics
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        metrics = {
            "profitability": {
                "profit_margins": info.get("profitMargins", "N/A"),
                "operating_margins": info.get("operatingMargins", "N/A"),
                "gross_margins": info.get("grossMargins", "N/A"),
                "roe": info.get("returnOnEquity", "N/A"),
                "roa": info.get("returnOnAssets", "N/A")
            },
            "valuation": {
                "trailing_pe": info.get("trailingPE", "N/A"),
                "forward_pe": info.get("forwardPE", "N/A"),
                "peg_ratio": info.get("pegRatio", "N/A"),
                "price_to_book": info.get("priceToBook", "N/A"),
                "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
                "ev_to_revenue": info.get("enterpriseToRevenue", "N/A"),
                "ev_to_ebitda": info.get("enterpriseToEbitda", "N/A")
            },
            "growth": {
                "revenue_growth": info.get("revenueGrowth", "N/A"),
                "earnings_growth": info.get("earningsGrowth", "N/A"),
                "revenue_per_share": info.get("revenuePerShare", "N/A"),
                "earnings_per_share": info.get("trailingEps", "N/A")
            },
            "financial_health": {
                "total_cash": info.get("totalCash", 0),
                "total_debt": info.get("totalDebt", 0),
                "debt_to_equity": info.get("debtToEquity", "N/A"),
                "current_ratio": info.get("currentRatio", "N/A"),
                "quick_ratio": info.get("quickRatio", "N/A")
            },
            "analyst_recommendations": {
                "target_high": info.get("targetHighPrice", "N/A"),
                "target_low": info.get("targetLowPrice", "N/A"),
                "target_mean": info.get("targetMeanPrice", "N/A"),
                "target_median": info.get("targetMedianPrice", "N/A"),
                "recommendation": info.get("recommendationKey", "N/A"),
                "number_of_analysts": info.get("numberOfAnalystOpinions", "N/A")
            }
        }
        
        return metrics
    except Exception as e:
        raise Exception(f"Error fetching key metrics for {ticker}: {str(e)}")


def get_historical_data(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """
    Get historical price data
    
    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        Dictionary with historical data
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {"error": "No historical data available"}
        
        return {
            "data": hist.to_dict(),
            "period": period,
            "start_date": str(hist.index[0].date()),
            "end_date": str(hist.index[-1].date())
        }
    except Exception as e:
        raise Exception(f"Error fetching historical data for {ticker}: {str(e)}")


def get_competitors(ticker: str) -> list[str]:
    """
    Try to identify competitors based on sector/industry
    Note: yfinance doesn't provide direct competitor data, so this is a basic implementation
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of potential competitor tickers
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # This is a placeholder - in a production app, you'd use a more sophisticated method
        # or API that provides competitor information
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        
        # Return basic info for now - agents will need to search for competitors
        return {
            "sector": sector,
            "industry": industry,
            "note": "Competitor identification requires web scraping or additional APIs"
        }
    except Exception as e:
        return {"error": str(e)}

