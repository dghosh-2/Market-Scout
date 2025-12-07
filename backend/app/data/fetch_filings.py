import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
from datetime import datetime


def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Get CIK (Central Index Key) from ticker symbol
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        CIK string or None
    """
    try:
        # Use SEC's ticker to CIK mapping
        url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "company": ticker,
            "type": "",
            "dateb": "",
            "owner": "exclude",
            "count": "1",
            "search_text": ""
        }
        
        headers = {
            "User-Agent": "Stock Research App contact@example.com"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Extract CIK from response
            match = re.search(r'CIK=(\d+)', response.text)
            if match:
                cik = match.group(1).zfill(10)  # Pad with zeros to 10 digits
                return cik
        
        return None
    except Exception as e:
        print(f"Error getting CIK for {ticker}: {str(e)}")
        return None


def get_latest_filing(ticker: str, filing_type: str = "10-K") -> Optional[Dict[str, Any]]:
    """
    Get the latest SEC filing for a company
    
    Args:
        ticker: Stock ticker symbol
        filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
        
    Returns:
        Dictionary with filing information
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return {"error": f"Could not find CIK for ticker {ticker}"}
        
        # Get filing list
        url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": filing_type,
            "dateb": "",
            "owner": "exclude",
            "count": "1"
        }
        
        headers = {
            "User-Agent": "Stock Research App contact@example.com"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": "Failed to fetch filing from SEC"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the document link
        doc_table = soup.find('table', {'class': 'tableFile2'})
        if not doc_table:
            return {"error": f"No {filing_type} filings found"}
        
        # Get the first filing row
        rows = doc_table.find_all('tr')
        if len(rows) < 2:
            return {"error": "No filing data available"}
        
        # Extract filing date and document link
        filing_row = rows[1]
        cells = filing_row.find_all('td')
        
        filing_info = {
            "filing_type": filing_type,
            "filing_date": cells[3].text.strip() if len(cells) > 3 else "Unknown",
            "description": cells[2].text.strip() if len(cells) > 2 else "No description",
        }
        
        # Get document URL
        doc_link = cells[1].find('a', {'id': 'documentsbutton'})
        if doc_link:
            doc_url = "https://www.sec.gov" + doc_link['href']
            filing_info["document_url"] = doc_url
        
        return filing_info
        
    except Exception as e:
        return {"error": f"Error fetching filing: {str(e)}"}


def fetch_filing_content(filing_url: str, max_length: int = 100000) -> str:
    """
    Fetch the actual content of a filing
    
    Args:
        filing_url: URL to the filing document
        max_length: Maximum characters to fetch
        
    Returns:
        Filing text content
    """
    try:
        headers = {
            "User-Agent": "Stock Research App contact@example.com"
        }
        
        response = requests.get(filing_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return "Failed to fetch filing content"
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Content truncated for length...]"
        
        return text
        
    except Exception as e:
        return f"Error fetching content: {str(e)}"


def get_filing_summary(ticker: str, filing_type: str = "10-K") -> Dict[str, Any]:
    """
    Get a summary of the latest filing with key sections
    
    Args:
        ticker: Stock ticker symbol
        filing_type: Type of filing
        
    Returns:
        Dictionary with filing summary
    """
    try:
        filing_info = get_latest_filing(ticker, filing_type)
        
        if "error" in filing_info:
            return filing_info
        
        # For now, just return the filing info
        # In a production app, you'd fetch and parse key sections
        filing_info["summary"] = f"Latest {filing_type} filing for {ticker}"
        filing_info["note"] = "Full parsing requires downloading and analyzing the complete filing document"
        
        return filing_info
        
    except Exception as e:
        return {"error": f"Error getting filing summary: {str(e)}"}


def search_filings_for_keywords(ticker: str, keywords: List[str], filing_type: str = "10-K") -> Dict[str, Any]:
    """
    Search filing for specific keywords (useful for risk analysis)
    
    Args:
        ticker: Stock ticker symbol
        keywords: List of keywords to search for
        filing_type: Type of filing
        
    Returns:
        Dictionary with search results
    """
    try:
        filing_info = get_latest_filing(ticker, filing_type)
        
        if "error" in filing_info or "document_url" not in filing_info:
            return filing_info
        
        # This is a basic implementation
        # In production, you'd want more sophisticated text analysis
        
        return {
            "ticker": ticker,
            "filing_type": filing_type,
            "keywords": keywords,
            "note": "Keyword search requires downloading and analyzing the full filing",
            "filing_info": filing_info
        }
        
    except Exception as e:
        return {"error": f"Error searching filings: {str(e)}"}

