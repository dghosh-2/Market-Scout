import json
from typing import Dict, Any, List, Optional, Set
from openai import OpenAI
from app.config.settings import get_settings
from app.agents.tools import TOOL_DEFINITIONS, execute_tool, get_portfolio_context

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

# Topics that warrant a dedicated custom section (not already covered in standard sections)
CUSTOM_SECTION_TOPICS = {
    "leadership": ["leadership", "ceo", "executive", "management", "board", "directors", "c-suite", "founder"],
    "compensation": ["compensation", "salary", "pay", "bonus", "stock options", "executive pay"],
    "esg": ["esg", "environmental", "social", "governance", "sustainability", "carbon", "climate", "diversity"],
    "competitors": ["competitors", "competition", "market share", "rivals", "vs", "compared to"],
    "products": ["products", "product line", "services", "offerings", "pipeline", "roadmap"],
    "patents": ["patents", "intellectual property", "ip", "innovation", "r&d", "research"],
    "legal": ["legal", "lawsuits", "litigation", "regulatory", "sec", "compliance", "investigation"],
    "acquisitions": ["acquisitions", "mergers", "m&a", "buyout", "takeover", "deal"],
    "international": ["international", "global", "overseas", "expansion", "markets", "geographic"],
    "supply_chain": ["supply chain", "suppliers", "manufacturing", "logistics", "inventory"],
}

# Topics that are elaborations of existing sections (don't need custom section)
EXISTING_SECTION_TOPICS = [
    "dividend", "growth", "revenue", "earnings", "profit", "valuation", "pe ratio", "price",
    "risk", "volatility", "beta", "debt", "financial", "balance sheet", "cash flow",
    "news", "sentiment", "analyst", "recommendation", "target price", "outlook"
]


def detect_custom_section_topic(custom_request: str) -> tuple[str, str]:
    """
    Detect if the custom request requires a dedicated section.
    Returns (section_title, topic_key) or (None, None) if no custom section needed.
    """
    if not custom_request:
        return None, None
    
    request_lower = custom_request.lower()
    
    # Check if it's just elaborating on existing sections
    for topic in EXISTING_SECTION_TOPICS:
        if topic in request_lower:
            return None, None
    
    # Check for custom section topics
    for topic_key, keywords in CUSTOM_SECTION_TOPICS.items():
        for keyword in keywords:
            if keyword in request_lower:
                # Generate a readable section title
                titles = {
                    "leadership": "Leadership & Management",
                    "compensation": "Executive Compensation",
                    "esg": "ESG & Sustainability",
                    "competitors": "Competitive Analysis",
                    "products": "Products & Services",
                    "patents": "Innovation & Intellectual Property",
                    "legal": "Legal & Regulatory",
                    "acquisitions": "M&A Activity",
                    "international": "International Operations",
                    "supply_chain": "Supply Chain Analysis",
                }
                return titles.get(topic_key, custom_request.title()), topic_key
    
    # If custom request exists but doesn't match known patterns, create a custom section anyway
    if len(custom_request) > 10:
        title = " ".join(custom_request.split()[:3])
        return title, "custom"
    
    return None, None


def run_master_agent(
    ticker: str,
    company_name: str,
    user_query: str,
    custom_request: str = "",
    omit_sections: Optional[List[str]] = None,
    add_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Master agent that uses tool calling to gather data and generate analysis."""
    omit: Set[str] = {str(s).lower() for s in (omit_sections or []) if s}
    add_list = [str(s) for s in (add_sections or []) if s]

    # Gather all data first (respect omissions)
    gathered_data: Dict[str, Any] = {}
    if "company" not in omit:
        gathered_data["company_info"] = execute_tool("get_company_info", {"ticker": ticker})
    else:
        gathered_data["company_info"] = {"omitted": True}

    if "financials" not in omit:
        gathered_data["financials"] = execute_tool("get_financials", {"ticker": ticker})
    else:
        gathered_data["financials"] = {"omitted": True}

    if "risks" not in omit:
        gathered_data["risks"] = execute_tool("get_risks", {"ticker": ticker})
    else:
        gathered_data["risks"] = {"omitted": True}

    if "news" not in omit:
        gathered_data["news"] = execute_tool("get_news", {"ticker": ticker})
    else:
        gathered_data["news"] = {"omitted": True, "articles": []}
    
    if custom_request:
        gathered_data["other"] = execute_tool("get_other", {"ticker": ticker, "custom_request": custom_request})
    
    # Get portfolio context
    portfolio_context = get_portfolio_context()
    gathered_data["portfolio"] = portfolio_context
    
    # Detect if we need a custom section
    custom_section_title, custom_topic = detect_custom_section_topic(custom_request)
    
    # Generate analysis
    analysis = generate_analysis(
        ticker,
        company_name,
        user_query,
        custom_request,
        gathered_data,
        portfolio_context,
        custom_section_title,
        omit_sections=omit,
        add_sections=add_list,
    )
    
    # Generate news reflections
    news_data = gathered_data.get("news", {})
    if "news" not in omit and news_data.get("articles"):
        news_reflections = generate_news_reflections(ticker, company_name, news_data["articles"][:5])
        analysis["news_reflections"] = news_reflections
    
    # Store custom section title in analysis
    if custom_section_title:
        analysis["custom_section_title"] = custom_section_title
    
    return {
        "ticker": ticker,
        "company_name": company_name,
        "user_query": user_query,
        "custom_request": custom_request,
        "raw_data": gathered_data,
        "analysis": analysis,
        "portfolio_context": portfolio_context
    }


def generate_news_reflections(ticker: str, company_name: str, articles: List[Dict]) -> List[Dict]:
    """Generate AI reflections on what each news article means for the company's future."""
    if not articles:
        return []
    
    headlines = "\n".join([f"- {a['title']} ({a['publisher']})" for a in articles if a.get('title')])
    
    if not headlines:
        return []
    
    prompt = f"""For {company_name} ({ticker}), analyze these recent news headlines and provide a brief 1-2 sentence reflection on what each means for the company's future performance.

Headlines:
{headlines}

For each headline, provide a concise reflection on its potential impact (positive, negative, or neutral) on the company's stock performance and business outlook.

Format your response as:
HEADLINE: [exact headline text]
REFLECTION: [your 1-2 sentence analysis]

Repeat for each headline."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        reflections = []
        
        current_headline = None
        current_reflection = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith('HEADLINE:'):
                if current_headline and current_reflection:
                    reflections.append({
                        "headline": current_headline,
                        "reflection": current_reflection
                    })
                current_headline = line.split(':', 1)[1].strip() if ':' in line else ""
                current_reflection = None
            elif line.upper().startswith('REFLECTION:'):
                current_reflection = line.split(':', 1)[1].strip() if ':' in line else ""
        
        # Don't forget the last one
        if current_headline and current_reflection:
            reflections.append({
                "headline": current_headline,
                "reflection": current_reflection
            })
        
        # Match reflections back to original articles
        result = []
        for article in articles:
            matched_reflection = ""
            for ref in reflections:
                # Fuzzy match - check if key words from headline appear
                if article.get('title') and ref['headline']:
                    title_words = set(article['title'].lower().split()[:5])
                    ref_words = set(ref['headline'].lower().split()[:5])
                    if len(title_words & ref_words) >= 2:
                        matched_reflection = ref['reflection']
                        break
            
            result.append({
                "title": article.get('title', ''),
                "publisher": article.get('publisher', ''),
                "published": article.get('published', ''),
                "reflection": matched_reflection or "This news may impact investor sentiment and should be monitored for further developments."
            })
        
        return result
        
    except Exception as e:
        # Return articles with generic reflections on error
        return [{
            "title": a.get('title', ''),
            "publisher": a.get('publisher', ''),
            "published": a.get('published', ''),
            "reflection": "Monitor this development for potential impact on stock performance."
        } for a in articles]


def generate_analysis(
    ticker: str,
    company_name: str,
    user_query: str,
    custom_request: str,
    data: Dict[str, Any],
    portfolio_context: Dict[str, Any] = None,
    custom_section_title: str = None,
    omit_sections: Optional[Set[str]] = None,
    add_sections: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Generate written analysis sections from gathered data"""
    omit = omit_sections or set()
    add_list = add_sections or []

    data_summary = json.dumps(data, indent=2, default=str)[:12000]

    omit_lines = []
    if "company" in omit:
        omit_lines.append("COMPANY_OVERVIEW (do not include this section at all)")
    if "financials" in omit:
        omit_lines.append("FINANCIAL_ANALYSIS (do not include this section at all)")
    if "risks" in omit:
        omit_lines.append("RISK_ASSESSMENT (do not include this section at all)")
    if "news" in omit:
        omit_lines.append("NEWS_ANALYSIS (do not include this section at all)")
    if "competitors" in omit:
        omit_lines.append(
            "any dedicated competitive landscape / competitor benchmarking section "
            "(you may still mention competition briefly inside other sections if needed)"
        )
    omit_instruction = ""
    if omit_lines:
        omit_instruction = (
            "\nOMIT THESE SECTIONS ENTIRELY (do not print their headers or body):\n- "
            + "\n- ".join(omit_lines)
        )

    add_instruction = ""
    if add_list:
        add_instruction = (
            f"\nADDITIONAL USER-REQUESTED TOPICS:\nThe user asked to also cover: {', '.join(add_list)}.\n"
            "Include a section with header exactly:\nUSER_TOPICS:\n"
            "with 2-4 paragraphs addressing these topics with specifics.\n"
        )
    
    # Build portfolio section prompt if portfolio exists
    portfolio_prompt = ""
    if portfolio_context and portfolio_context.get("holdings"):
        portfolio_summary = json.dumps(portfolio_context, indent=2, default=str)[:3000]
        portfolio_prompt = f"""

PORTFOLIO_FIT:
The user has an existing portfolio. Analyze how {company_name} ({ticker}) would fit into their current holdings:
{portfolio_summary}

Write 2-3 paragraphs analyzing:
1. Sector diversification - does this stock add new sector exposure or increase concentration?
2. Correlation and risk - how might this stock's volatility interact with existing holdings?
3. Portfolio balance - considering the user's current allocations, would adding this stock improve or worsen their portfolio balance?
4. Specific recommendation on position sizing if adding to portfolio."""
    else:
        portfolio_prompt = """

PORTFOLIO_FIT:
The user does not have any existing portfolio holdings tracked. Write 1 paragraph suggesting that they can add their holdings in the Portfolio tab to receive personalized portfolio fit analysis in future reports."""
    
    # Build custom section prompt if needed
    custom_section_prompt = ""
    if custom_section_title and custom_request:
        custom_section_prompt = f"""

CUSTOM_SECTION:
The user specifically requested information about: {custom_request}
Section Title: {custom_section_title}

Write 2-3 detailed paragraphs addressing this specific request. Use any relevant data available and provide actionable insights. Be thorough and specific to what the user asked for."""
    
    analysis_prompt = f"""You are a senior investment analyst writing a research report for {company_name} ({ticker}).

DATA:
{data_summary}

USER REQUEST: {user_query}
{f'SPECIFIC FOCUS: {custom_request}' if custom_request else ''}
{omit_instruction}
{add_instruction}

Write a professional stock research report. Output ONLY plain text paragraphs, NOT JSON or bullet points.

Write these sections as flowing paragraphs (skip any section you were told to OMIT entirely — do not include its header or text):

RECOMMENDATION:
Write 2-3 paragraphs. Start with a clear BUY, HOLD, or SELL recommendation. Explain the key reasons supporting this recommendation. Include target price if data supports it.

COMPANY_OVERVIEW:
Write 2-3 paragraphs about what the company does, its market position, competitive advantages, and key products/services.

FINANCIAL_ANALYSIS:
Write 2-3 paragraphs analyzing revenue, earnings, margins, valuation (P/E, P/B ratios), balance sheet health, and cash flow. Use specific numbers from the data.

RISK_ASSESSMENT:
Write 2-3 paragraphs about key investment risks including market risks, financial risks (debt, liquidity), competitive risks, and any governance concerns.

NEWS_ANALYSIS:
Write 1-2 paragraphs about recent news, market sentiment, and potential upcoming catalysts.
{custom_section_prompt}{portfolio_prompt}

Format your response EXACTLY like this (with section headers in caps followed by colon). Only include headers for sections you actually write:

RECOMMENDATION:
[your paragraphs here]

COMPANY_OVERVIEW:
[your paragraphs here]

FINANCIAL_ANALYSIS:
[your paragraphs here]

RISK_ASSESSMENT:
[your paragraphs here]

NEWS_ANALYSIS:
[your paragraphs here]
{f'''
CUSTOM_SECTION:
[your paragraphs addressing the custom request here]
''' if custom_section_title else ''}
{f'''
USER_TOPICS:
[your paragraphs here]
''' if add_list else ''}
PORTFOLIO_FIT:
[your paragraphs here]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_prompt}],
        max_tokens=3500,
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    
    # Parse sections
    sections = {
        "recommendation": "",
        "company_overview": "",
        "financial_analysis": "",
        "risk_assessment": "",
        "news_analysis": "",
        "custom_section": "",
        "user_topics": "",
        "portfolio_fit": ""
    }
    
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        line_upper = line.strip().upper()
        if line_upper.startswith('RECOMMENDATION:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "recommendation"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('COMPANY_OVERVIEW:') or line_upper.startswith('COMPANY OVERVIEW:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "company_overview"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('FINANCIAL_ANALYSIS:') or line_upper.startswith('FINANCIAL ANALYSIS:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "financial_analysis"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('RISK_ASSESSMENT:') or line_upper.startswith('RISK ASSESSMENT:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "risk_assessment"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('NEWS_ANALYSIS:') or line_upper.startswith('NEWS ANALYSIS:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "news_analysis"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('CUSTOM_SECTION:') or line_upper.startswith('CUSTOM SECTION:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "custom_section"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('USER_TOPICS:') or line_upper.startswith('USER TOPICS:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "user_topics"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif line_upper.startswith('PORTFOLIO_FIT:') or line_upper.startswith('PORTFOLIO FIT:'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "portfolio_fit"
            current_content = [line.split(':', 1)[1].strip()] if ':' in line else []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Fallback if parsing failed
    if not any(sections.values()):
        sections["recommendation"] = content
    
    return sections
