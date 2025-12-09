import json
from typing import Dict, Any, List
from openai import OpenAI
from app.config.settings import get_settings
from app.agents.tools import TOOL_DEFINITIONS, execute_tool, get_portfolio_context

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


def run_master_agent(ticker: str, company_name: str, user_query: str, custom_request: str = "") -> Dict[str, Any]:
    """Master agent that uses tool calling to gather data and generate analysis."""
    
    # Gather all data first
    gathered_data = {
        "company_info": execute_tool("get_company_info", {"ticker": ticker}),
        "financials": execute_tool("get_financials", {"ticker": ticker}),
        "risks": execute_tool("get_risks", {"ticker": ticker}),
        "news": execute_tool("get_news", {"ticker": ticker}),
    }
    
    if custom_request:
        gathered_data["other"] = execute_tool("get_other", {"ticker": ticker, "custom_request": custom_request})
    
    # Get portfolio context
    portfolio_context = get_portfolio_context()
    gathered_data["portfolio"] = portfolio_context
    
    # Generate analysis
    analysis = generate_analysis(ticker, company_name, user_query, custom_request, gathered_data, portfolio_context)
    
    return {
        "ticker": ticker,
        "company_name": company_name,
        "user_query": user_query,
        "custom_request": custom_request,
        "raw_data": gathered_data,
        "analysis": analysis,
        "portfolio_context": portfolio_context
    }


def generate_analysis(ticker: str, company_name: str, user_query: str, custom_request: str, data: Dict[str, Any], portfolio_context: Dict[str, Any] = None) -> Dict[str, str]:
    """Generate written analysis sections from gathered data"""
    
    data_summary = json.dumps(data, indent=2, default=str)[:12000]
    
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
    
    analysis_prompt = f"""You are a senior investment analyst writing a research report for {company_name} ({ticker}).

DATA:
{data_summary}

USER REQUEST: {user_query}
{f'SPECIFIC FOCUS: {custom_request}' if custom_request else ''}

Write a professional stock research report. Output ONLY plain text paragraphs, NOT JSON or bullet points.

Write these sections as flowing paragraphs:

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
{portfolio_prompt}

Format your response EXACTLY like this (with section headers in caps followed by colon):

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

PORTFOLIO_FIT:
[your paragraphs here]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_prompt}],
        max_tokens=3000,
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
