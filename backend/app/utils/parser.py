from bs4 import BeautifulSoup
import re
from typing import Optional


def clean_html(html_content: str) -> str:
    """
    Clean HTML content and extract plain text
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Cleaned plain text
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return html_content


def extract_text_from_filing(filing_content: str, max_length: int = 50000) -> str:
    """
    Extract relevant text from SEC filing
    
    Args:
        filing_content: Raw filing content (HTML or text)
        max_length: Maximum characters to return
        
    Returns:
        Extracted text
    """
    # Clean HTML if present
    text = clean_html(filing_content)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"
    
    return text.strip()


def extract_key_sections(filing_text: str, section_name: str) -> Optional[str]:
    """
    Extract specific section from SEC filing
    
    Args:
        filing_text: Full filing text
        section_name: Section to extract (e.g., "Risk Factors", "Business")
        
    Returns:
        Extracted section text or None
    """
    # Common SEC filing section patterns
    patterns = {
        "risk": r"(?i)item\s+1a\.?\s*risk\s+factors(.*?)(?=item\s+\d|$)",
        "business": r"(?i)item\s+1\.?\s*business(.*?)(?=item\s+\d|$)",
        "financial": r"(?i)item\s+7\.?\s*management'?s\s+discussion(.*?)(?=item\s+\d|$)",
        "properties": r"(?i)item\s+2\.?\s*properties(.*?)(?=item\s+\d|$)"
    }
    
    section_key = section_name.lower()
    
    if section_key not in patterns:
        return None
    
    match = re.search(patterns[section_key], filing_text, re.DOTALL)
    
    if match:
        section_text = match.group(1).strip()
        # Limit length
        if len(section_text) > 15000:
            section_text = section_text[:15000] + "... [truncated]"
        return section_text
    
    return None


def clean_financial_text(text: str) -> str:
    """
    Clean financial data text for better readability
    
    Args:
        text: Raw financial text
        
    Returns:
        Cleaned text
    """
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove page numbers and headers
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove table of contents artifacts
    text = re.sub(r'\.{5,}', '', text)
    
    return text.strip()


def format_number(num: float, prefix: str = "$", suffix: str = "") -> str:
    """
    Format large numbers for readability
    
    Args:
        num: Number to format
        prefix: Prefix (e.g., '$')
        suffix: Suffix (e.g., 'B', 'M')
        
    Returns:
        Formatted string
    """
    if num >= 1_000_000_000:
        return f"{prefix}{num / 1_000_000_000:.2f}B{suffix}"
    elif num >= 1_000_000:
        return f"{prefix}{num / 1_000_000:.2f}M{suffix}"
    elif num >= 1_000:
        return f"{prefix}{num / 1_000:.2f}K{suffix}"
    else:
        return f"{prefix}{num:.2f}{suffix}"

