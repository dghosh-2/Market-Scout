import json
import yfinance as yf
from typing import Tuple, Optional, Dict, Any
from openai import OpenAI
from app.config.settings import get_settings

settings = get_settings()

# Common company name -> ticker mappings for instant resolution
INSTANT_MAPPINGS = {
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
    "square": "SQ", "block": "SQ", "robinhood": "HOOD",
    "doordash": "DASH", "crowdstrike": "CRWD", "datadog": "DDOG",
    "twilio": "TWLO", "okta": "OKTA", "zscaler": "ZS",
    "mongodb": "MDB", "elastic": "ESTC", "cloudflare": "NET",
}


def resolve_company_to_ticker(query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve a company name or ticker to a valid ticker symbol using AI.
    Accepts: "Apple", "AAPL", "Taiwan Semiconductor", "TSMC", "that electric car company", etc.
    
    Returns: (ticker, company_name, error_message)
    """
    query = query.strip()
    if not query:
        return None, None, "Empty query provided"
    
    query_lower = query.lower().strip()
    
    # Check instant mappings first
    if query_lower in INSTANT_MAPPINGS:
        ticker = INSTANT_MAPPINGS[query_lower]
        return validate_and_get_info(ticker)
    
    # Check if it looks like a ticker (1-5 uppercase letters)
    potential_ticker = query.upper().replace(" ", "").replace(".", "").replace("-", "")
    if len(potential_ticker) <= 5 and potential_ticker.isalpha():
        result = validate_and_get_info(potential_ticker)
        if result[0]:
            return result
    
    # Use AI to resolve vague/descriptive queries
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""What is the stock ticker symbol for this company reference: "{query}"

If this refers to a publicly traded company (US exchanges preferred), respond with ONLY the ticker symbol (like AAPL, MSFT, TSM).
If you cannot determine a valid stock ticker, respond with: UNKNOWN

Examples:
- "that electric car company" -> TSLA
- "the iPhone maker" -> AAPL
- "Elon Musk's car company" -> TSLA
- "the search engine company" -> GOOGL
- "Taiwan chip maker" -> TSM
- "the AI chip company" -> NVDA
- "Jensen Huang's company" -> NVDA
- "the cloud computing giant from Seattle" -> AMZN
- "Zuckerberg's company" -> META
- "random gibberish" -> UNKNOWN

Your response (ticker symbol only, no explanation):"""
            }],
            max_tokens=10,
            temperature=0
        )
        
        ai_ticker = response.choices[0].message.content.strip().upper()
        # Clean up any extra text the model might add
        ai_ticker = ai_ticker.split()[0] if ai_ticker else ""
        ai_ticker = ''.join(c for c in ai_ticker if c.isalpha() or c == '-')
        
        if ai_ticker and ai_ticker != "UNKNOWN" and len(ai_ticker) <= 6:
            result = validate_and_get_info(ai_ticker)
            if result[0]:
                return result
    except Exception:
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
    """
    Parse user query to extract company/ticker and custom requests.
    Handles natural language queries like:
    - "What are Apple's growth prospects?"
    - "Tell me about that electric car company's financials"
    - "Analyze TSLA - focus on competition"
    - "the AI chip company leadership and compensation"
    """
    query = query.strip()
    if not query:
        return {
            "company_query": "",
            "custom_request": "",
            "omissions": [],
            "add_sections": [],
            "original_query": query
        }
    
    # First try explicit separators (fast path for structured queries)
    separators = [' - ', ' -- ', ': ', ' | ']
    for sep in separators:
        if sep in query:
            parts = query.split(sep, 1)
            company_part = parts[0].strip()
            custom_request = parts[1].strip() if len(parts) > 1 else ""
            
            # Parse omissions and additions from the custom request
            omissions, add_sections = _parse_modifiers(custom_request)
            
            return {
                "company_query": company_part,
                "custom_request": custom_request,
                "omissions": omissions,
                "add_sections": add_sections,
                "original_query": query
            }
    
    # Check if it's just a simple ticker or company name (no complex query)
    query_lower = query.lower().strip()
    if query_lower in INSTANT_MAPPINGS:
        return {
            "company_query": query,
            "custom_request": "",
            "omissions": [],
            "add_sections": [],
            "original_query": query
        }
    
    # Check if it looks like a simple ticker
    potential_ticker = query.upper().replace(" ", "").replace(".", "")
    if len(potential_ticker) <= 5 and potential_ticker.isalpha():
        return {
            "company_query": query,
            "custom_request": "",
            "omissions": [],
            "add_sections": [],
            "original_query": query
        }
    
    # For complex natural language queries, use AI to parse
    parsed = _ai_parse_query(query)
    if parsed:
        omissions, add_sections = _parse_modifiers(parsed["custom_request"])
        return {
            "company_query": parsed["company_query"],
            "custom_request": parsed["custom_request"],
            "omissions": omissions,
            "add_sections": add_sections,
            "original_query": query
        }
    
    # Fallback: treat entire query as company query
    return {
        "company_query": query,
        "custom_request": "",
        "omissions": [],
        "add_sections": [],
        "original_query": query
    }


def _ai_parse_query(query: str) -> Optional[Dict[str, str]]:
    """
    Use AI to parse natural language queries and extract:
    - company_query: the company reference (name, ticker, or description)
    - custom_request: specific focus areas or questions
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Parse this stock research query and extract two parts:
1. company_query: The company reference (could be a name, ticker, or description like "that electric car company")
2. custom_request: Any specific focus areas, topics, or questions the user wants addressed (empty string if none)

Query: "{query}"

Examples:
- "What are Apple's growth prospects?" -> {{"company_query": "Apple", "custom_request": "growth prospects"}}
- "Tell me about that electric car company's financials" -> {{"company_query": "that electric car company", "custom_request": "financials"}}
- "AAPL" -> {{"company_query": "AAPL", "custom_request": ""}}
- "Analyze the Taiwan chip maker" -> {{"company_query": "Taiwan chip maker", "custom_request": ""}}
- "How is Nvidia doing with AI?" -> {{"company_query": "Nvidia", "custom_request": "AI performance and positioning"}}
- "What's happening with Tesla stock" -> {{"company_query": "Tesla", "custom_request": "recent developments and stock performance"}}
- "the search engine company leadership changes" -> {{"company_query": "the search engine company", "custom_request": "leadership changes"}}
- "Jensen Huang's company and their AI chips" -> {{"company_query": "Jensen Huang's company", "custom_request": "AI chips"}}
- "Microsoft cloud growth" -> {{"company_query": "Microsoft", "custom_request": "cloud growth"}}
- "is Amazon a good investment" -> {{"company_query": "Amazon", "custom_request": "investment analysis and recommendation"}}

Respond with ONLY a JSON object, no other text:"""
            }],
            max_tokens=150,
            temperature=0
        )
        
        content = response.choices[0].message.content.strip()
        # Clean up markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        parsed = json.loads(content)
        if "company_query" in parsed:
            return {
                "company_query": str(parsed.get("company_query", "")).strip(),
                "custom_request": str(parsed.get("custom_request", "")).strip()
            }
    except Exception:
        pass
    
    return None


def _parse_modifiers(custom_request: str) -> Tuple[list, list]:
    """Extract omissions and add_sections from custom request text."""
    omissions = []
    add_sections = []
    
    if not custom_request:
        return omissions, add_sections
    
    cr_lower = custom_request.lower()
    
    # Parse omissions
    omit_patterns = ['omit ', 'skip ', 'no ', 'without ', "don't include ", "exclude "]
    for pattern in omit_patterns:
        if pattern in cr_lower:
            for section in ['news', 'financials', 'risks', 'company', 'competitors']:
                if section in cr_lower:
                    if section not in omissions:
                        omissions.append(section)
    
    # Parse add_sections
    if "add section" in cr_lower or "include section" in cr_lower or "also cover" in cr_lower:
        hint = custom_request
        for sep in [":", "—", " - "]:
            if sep in hint:
                hint = hint.split(sep)[-1].strip()
        if hint and len(hint) > 3 and hint != custom_request:
            add_sections.append(hint.strip())
    
    return omissions, add_sections
