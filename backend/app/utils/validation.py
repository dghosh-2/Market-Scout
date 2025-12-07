import yfinance as yf
from typing import Tuple, Optional, Dict, Any
from openai import OpenAI
from app.config.settings import get_settings

settings = get_settings()


def resolve_company_to_ticker(query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve a company name or ticker to a valid ticker symbol using AI.
    Accepts: "Apple", "AAPL", "Taiwan Semiconductor", "TSMC", "that electric car company", etc.
    
    Returns: (ticker, company_name, error_message)
    """
    query = query.strip()
    if not query:
        return None, None, "Empty query provided"
    
    # Common mappings for instant resolution
    instant_mappings = {
        "tsmc": "TSM", "taiwan semiconductor": "TSM", "taiwan semi": "TSM",
        "google": "GOOGL", "alphabet": "GOOGL",
        "facebook": "META", "meta": "META",
        "amazon": "AMZN", "apple": "AAPL", "microsoft": "MSFT",
        "nvidia": "NVDA", "tesla": "TSLA",
        "berkshire": "BRK-B", "berkshire hathaway": "BRK-B",
        "jp morgan": "JPM", "jpmorgan": "JPM",
        "johnson and johnson": "JNJ", "johnson & johnson": "JNJ",
        "coca cola": "KO", "coca-cola": "KO",
        "walmart": "WMT", "disney": "DIS", "netflix": "NFLX",
        "adobe": "ADBE", "salesforce": "CRM", "intel": "INTC",
        "amd": "AMD", "advanced micro devices": "AMD",
        "paypal": "PYPL", "broadcom": "AVGO", "costco": "COST",
        "pepsi": "PEP", "pepsico": "PEP", "oracle": "ORCL",
        "cisco": "CSCO", "verizon": "VZ", "at&t": "T", "att": "T",
        "nike": "NKE", "mcdonalds": "MCD", "starbucks": "SBUX",
        "boeing": "BA", "goldman sachs": "GS", "morgan stanley": "MS",
        "bank of america": "BAC", "wells fargo": "WFC",
        "uber": "UBER", "lyft": "LYFT", "airbnb": "ABNB",
        "snowflake": "SNOW", "palantir": "PLTR", "spotify": "SPOT",
        "zoom": "ZM", "shopify": "SHOP", "coinbase": "COIN",
    }
    
    query_lower = query.lower().strip()
    
    # Check instant mappings
    if query_lower in instant_mappings:
        ticker = instant_mappings[query_lower]
        return validate_and_get_info(ticker)
    
    # Check if it looks like a ticker (1-5 uppercase letters)
    potential_ticker = query.upper().replace(" ", "").replace(".", "")
    if len(potential_ticker) <= 5 and potential_ticker.isalpha():
        result = validate_and_get_info(potential_ticker)
        if result[0]:
            return result
    
    # Use AI to resolve vague queries
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""What is the stock ticker symbol for: "{query}"

If this refers to a publicly traded company, respond with ONLY the ticker symbol (like AAPL, MSFT, TSM).
If you cannot determine a valid US stock ticker, respond with: UNKNOWN

Examples:
- "that electric car company" -> TSLA
- "the iPhone maker" -> AAPL
- "Elon Musk's car company" -> TSLA
- "the search engine company" -> GOOGL
- "Taiwan chip maker" -> TSM
- "random gibberish" -> UNKNOWN

Your response (ticker only):"""
            }],
            max_tokens=10,
            temperature=0
        )
        
        ai_ticker = response.choices[0].message.content.strip().upper()
        
        if ai_ticker and ai_ticker != "UNKNOWN" and len(ai_ticker) <= 5:
            result = validate_and_get_info(ai_ticker)
            if result[0]:
                return result
    except:
        pass
    
    return None, None, f"Could not find a valid ticker for '{query}'. Try using the stock symbol directly (e.g., AAPL, MSFT, TSM)."


def validate_and_get_info(ticker: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Validate ticker and get company name"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            return None, None, f"No data found for ticker '{ticker}'"
        
        company_name = info.get('longName') or info.get('shortName') or info.get('displayName')
        
        if not company_name:
            return None, None, f"'{ticker}' does not appear to be a valid stock"
        
        return ticker, company_name, None
        
    except Exception as e:
        return None, None, f"Error validating ticker '{ticker}': {str(e)}"


def parse_user_query(query: str) -> Dict[str, Any]:
    """Parse user query to extract company/ticker and custom requests."""
    query = query.strip()
    
    separators = [' - ', ' -- ', ': ', ' | ']
    company_part = query
    custom_request = ""
    
    for sep in separators:
        if sep in query:
            parts = query.split(sep, 1)
            company_part = parts[0].strip()
            custom_request = parts[1].strip() if len(parts) > 1 else ""
            break
    
    omissions = []
    omit_patterns = ['omit ', 'skip ', 'no ', 'without ', "don't include "]
    for pattern in omit_patterns:
        if pattern in custom_request.lower():
            for section in ['news', 'financials', 'risks', 'company', 'competitors']:
                if section in custom_request.lower():
                    omissions.append(section)
    
    return {
        "company_query": company_part,
        "custom_request": custom_request,
        "omissions": omissions,
        "original_query": query
    }
