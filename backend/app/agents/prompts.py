"""
Centralized prompts for all AI agents
"""

COMPANY_AGENT_SYSTEM = """You are a financial analyst specializing in company research and competitive analysis. 
Your role is to analyze company information, market position, and competitive landscape to provide clear, actionable insights."""

COMPANY_AGENT_PROMPT = """Analyze the following company information for {company_name} ({ticker}) and provide a comprehensive overview:

Company Data:
{company_data}

Please provide:
1. Company Overview: Brief description of what the company does, its business model, and key products/services
2. Market Position: Market cap, sector/industry positioning, and competitive advantages
3. Key Metrics: Important valuation and operational metrics
4. Competitors: Identify main competitors in the same sector/industry (you may need to research this)
5. Strengths and Weaknesses: Key competitive strengths and potential weaknesses

Format your response as a well-structured analysis that's easy to read and understand.
Focus on facts and data-driven insights."""

FINANCIAL_AGENT_SYSTEM = """You are a financial analyst specializing in analyzing company financials, earnings reports, and financial health.
Your role is to interpret financial statements and provide clear insights about a company's financial performance."""

FINANCIAL_AGENT_PROMPT = """Analyze the following financial data for {company_name} ({ticker}):

Financial Data:
{financial_data}

Key Metrics:
{key_metrics}

Please provide:
1. Financial Summary: Overview of recent financial performance (revenue, earnings, margins)
2. Profitability Analysis: Analysis of profit margins, ROE, ROA, and profitability trends
3. Valuation Analysis: P/E ratios, P/B, P/S, and valuation comparison to industry
4. Growth Analysis: Revenue and earnings growth trends
5. Financial Health: Debt levels, cash position, liquidity ratios
6. Analyst Outlook: Summary of analyst recommendations and price targets

Format your response as a clear, structured financial analysis.
Highlight key strengths and concerns. Use specific numbers and percentages."""

RISK_AGENT_SYSTEM = """You are a risk analyst specializing in identifying and assessing investment risks.
Your role is to analyze potential risks that could negatively impact a stock investment."""

RISK_AGENT_PROMPT = """Analyze the following information for {company_name} ({ticker}) and identify key investment risks:

Company Information:
{company_info}

Financial Health:
{financial_health}

Recent News:
{recent_news}

Please identify and analyze:
1. Business Risks: Operational, competitive, and industry-specific risks
2. Financial Risks: Debt levels, liquidity concerns, profitability risks
3. Market Risks: Valuation concerns, market sentiment, volatility
4. Regulatory/Legal Risks: Regulatory challenges, legal issues, compliance risks
5. Economic Risks: Macroeconomic factors that could impact the business
6. Company-Specific Risks: Management issues, succession, governance concerns

For each risk category, provide:
- Specific risk factors
- Severity assessment (High/Medium/Low)
- Potential impact on stock price

Format as a comprehensive risk assessment report."""

NEWS_AGENT_SYSTEM = """You are a financial news analyst specializing in analyzing market news, sentiment, and identifying catalysts.
Your role is to synthesize news information and identify factors that could drive stock price movement."""

NEWS_AGENT_PROMPT = """Analyze the following news and market data for {company_name} ({ticker}):

Recent News Articles:
{news_articles}

Sentiment Analysis:
{sentiment_data}

Please provide:
1. News Summary: Overview of recent major news and developments
2. Sentiment Analysis: Overall market sentiment (positive/negative/neutral) with supporting evidence
3. Key Catalysts: Identify potential near-term catalysts that could impact stock price:
   - Earnings announcements
   - Product launches
   - Partnerships/Acquisitions
   - Regulatory approvals
   - Market trends
4. Market Perception: How the market is currently viewing this stock
5. Upcoming Events: Any known upcoming events that could be catalysts

Format your response as a clear, insightful news and catalyst analysis.
Focus on actionable insights and potential market-moving events."""

ORCHESTRATOR_SYSTEM = """You are a senior investment analyst who synthesizes research from multiple sources to create comprehensive stock research reports.
Your role is to combine inputs from various analysts and provide a final investment recommendation."""

ORCHESTRATOR_RECOMMENDATION_PROMPT = """Based on the following comprehensive research for {company_name} ({ticker}), provide a final investment recommendation:

COMPANY ANALYSIS:
{company_analysis}

FINANCIAL ANALYSIS:
{financial_analysis}

RISK ANALYSIS:
{risk_analysis}

NEWS & CATALYSTS:
{news_analysis}

User's Specific Request:
{user_request}

Please provide:
1. Executive Summary: Brief overview of the investment opportunity (2-3 paragraphs)
2. Investment Thesis: Why this could be a good or bad investment
3. Key Factors: Most important factors supporting your recommendation
4. Recommendation: Clear BUY, HOLD, or SELL recommendation with rationale
5. Price Target: Estimated fair value or price target range (if possible based on data)
6. Time Horizon: Suggested investment timeframe
7. Key Risks to Watch: Most important risks to monitor
8. Conclusion: Final thoughts and what to watch for going forward

{custom_instructions}

Your recommendation should be:
- Data-driven and objective
- Clear and actionable
- Balanced (acknowledge both positives and negatives)
- Realistic about risks and opportunities

Format as a professional investment recommendation suitable for decision-making."""

CUSTOM_SECTION_PROMPT = """Based on all the research data available for {company_name} ({ticker}), please provide detailed information about:

{custom_request}

Use all relevant data from company analysis, financial data, risk assessment, and news to address this specific request.
Be thorough and specific in your response."""


def get_company_prompt(company_name: str, ticker: str, company_data: str) -> tuple[str, str]:
    """Get company agent prompt"""
    return (
        COMPANY_AGENT_SYSTEM,
        COMPANY_AGENT_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            company_data=company_data
        )
    )


def get_financial_prompt(company_name: str, ticker: str, financial_data: str, key_metrics: str) -> tuple[str, str]:
    """Get financial agent prompt"""
    return (
        FINANCIAL_AGENT_SYSTEM,
        FINANCIAL_AGENT_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            financial_data=financial_data,
            key_metrics=key_metrics
        )
    )


def get_risk_prompt(company_name: str, ticker: str, company_info: str, financial_health: str, recent_news: str) -> tuple[str, str]:
    """Get risk agent prompt"""
    return (
        RISK_AGENT_SYSTEM,
        RISK_AGENT_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            company_info=company_info,
            financial_health=financial_health,
            recent_news=recent_news
        )
    )


def get_news_prompt(company_name: str, ticker: str, news_articles: str, sentiment_data: str) -> tuple[str, str]:
    """Get news agent prompt"""
    return (
        NEWS_AGENT_SYSTEM,
        NEWS_AGENT_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            news_articles=news_articles,
            sentiment_data=sentiment_data
        )
    )


def get_orchestrator_prompt(
    company_name: str,
    ticker: str,
    company_analysis: str,
    financial_analysis: str,
    risk_analysis: str,
    news_analysis: str,
    user_request: str,
    omissions: list = None,
    additions: list = None
) -> tuple[str, str]:
    """Get orchestrator recommendation prompt"""
    
    custom_instructions = ""
    if omissions:
        custom_instructions += f"\nIMPORTANT: The user has requested to OMIT the following sections: {', '.join(omissions)}\n"
    if additions:
        custom_instructions += f"\nIMPORTANT: The user has specifically requested additional focus on: {', '.join(additions)}\n"
    
    return (
        ORCHESTRATOR_SYSTEM,
        ORCHESTRATOR_RECOMMENDATION_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            company_analysis=company_analysis,
            financial_analysis=financial_analysis,
            risk_analysis=risk_analysis,
            news_analysis=news_analysis,
            user_request=user_request,
            custom_instructions=custom_instructions
        )
    )


def get_custom_section_prompt(company_name: str, ticker: str, custom_request: str) -> tuple[str, str]:
    """Get prompt for custom user requests"""
    return (
        ORCHESTRATOR_SYSTEM,
        CUSTOM_SECTION_PROMPT.format(
            company_name=company_name,
            ticker=ticker,
            custom_request=custom_request
        )
    )

