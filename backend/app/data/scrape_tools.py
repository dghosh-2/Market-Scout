import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import time


def fetch_webpage(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch webpage content
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        HTML content or None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None


def parse_html_table(html_content: str, table_class: Optional[str] = None) -> List[List[str]]:
    """
    Parse HTML table into list of lists
    
    Args:
        html_content: HTML content containing table
        table_class: CSS class of the table to parse
        
    Returns:
        List of rows (each row is a list of cell values)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if table_class:
            table = soup.find('table', {'class': table_class})
        else:
            table = soup.find('table')
        
        if not table:
            return []
        
        rows = []
        for tr in table.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:
                rows.append(row)
        
        return rows
    except Exception as e:
        print(f"Error parsing table: {str(e)}")
        return []


def search_google(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Search Google and return results
    Note: This is a basic implementation. For production, use Google Custom Search API
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        List of search results
    """
    # Placeholder - in production, use Google Custom Search API or alternative
    # This requires API key and proper implementation
    
    return [{
        "title": f"Search results for: {query}",
        "link": "",
        "snippet": "This is a placeholder. Integrate Google Custom Search API for actual results.",
        "note": "Use Google Custom Search API (https://developers.google.com/custom-search) for production"
    }]


def scrape_competitor_info(company_name: str) -> Dict[str, Any]:
    """
    Scrape competitor information
    Note: This would typically require specific scrapers for sources like:
    - Yahoo Finance
    - MarketWatch
    - Crunchbase
    - Bloomberg
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with competitor information
    """
    # Placeholder implementation
    # In production, scrape from multiple sources or use APIs
    
    return {
        "company": company_name,
        "competitors": [],
        "note": "Competitor data requires specialized web scraping or API integration",
        "suggested_sources": [
            "Yahoo Finance competitor section",
            "MarketWatch industry comparison",
            "Crunchbase similar companies",
            "SEC filings (10-K, Item 1 - Business section)"
        ]
    }


def scrape_stock_screener(filters: Dict[str, Any]) -> List[str]:
    """
    Scrape stock screener results
    
    Args:
        filters: Dictionary of filter criteria
        
    Returns:
        List of ticker symbols matching criteria
    """
    # Placeholder for stock screener
    # In production, integrate with:
    # - Finviz
    # - Yahoo Finance Screener
    # - TradingView Screener
    
    return []


def extract_text_content(html: str) -> str:
    """
    Extract clean text content from HTML
    
    Args:
        html: HTML content
        
    Returns:
        Cleaned text
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text
    except Exception as e:
        return html


def rate_limit_request(delay: float = 1.0):
    """
    Add delay between requests to avoid rate limiting
    
    Args:
        delay: Delay in seconds
    """
    time.sleep(delay)

