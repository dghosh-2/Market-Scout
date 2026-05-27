"""Convergence node: merges technical + risk + news into the final analysis JSON."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set

from app.agents.state import ResearchState
from app.agents.tools import aget_other, get_portfolio_context
from app.telemetry.langfuse_client import observe, update_current_observation
from app.utils.async_llm import chat_completion

logger = logging.getLogger(__name__)

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

EXISTING_SECTION_TOPICS = [
    "dividend", "growth", "revenue", "earnings", "profit", "valuation", "pe ratio", "price",
    "risk", "volatility", "beta", "debt", "financial", "balance sheet", "cash flow",
    "news", "sentiment", "analyst", "recommendation", "target price", "outlook",
]

SECTION_TITLES = {
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


def _detect_custom_section_topic(custom_request: str) -> tuple[Optional[str], Optional[str]]:
    if not custom_request:
        return None, None
    request_lower = custom_request.lower()
    for topic in EXISTING_SECTION_TOPICS:
        if topic in request_lower:
            return None, None
    for topic_key, keywords in CUSTOM_SECTION_TOPICS.items():
        for keyword in keywords:
            if keyword in request_lower:
                return SECTION_TITLES.get(topic_key, custom_request.title()), topic_key
    if len(custom_request) > 10:
        return " ".join(custom_request.split()[:3]), "custom"
    return None, None


_SECTION_KEYS = [
    ("RECOMMENDATION:", "recommendation"),
    ("COMPANY_OVERVIEW:", "company_overview"),
    ("COMPANY OVERVIEW:", "company_overview"),
    ("FINANCIAL_ANALYSIS:", "financial_analysis"),
    ("FINANCIAL ANALYSIS:", "financial_analysis"),
    ("RISK_ASSESSMENT:", "risk_assessment"),
    ("RISK ASSESSMENT:", "risk_assessment"),
    ("NEWS_ANALYSIS:", "news_analysis"),
    ("NEWS ANALYSIS:", "news_analysis"),
    ("CUSTOM_SECTION:", "custom_section"),
    ("CUSTOM SECTION:", "custom_section"),
    ("USER_TOPICS:", "user_topics"),
    ("USER TOPICS:", "user_topics"),
    ("PORTFOLIO_FIT:", "portfolio_fit"),
    ("PORTFOLIO FIT:", "portfolio_fit"),
]


def _parse_sections(content: str) -> Dict[str, str]:
    sections: Dict[str, str] = {
        "recommendation": "",
        "company_overview": "",
        "financial_analysis": "",
        "risk_assessment": "",
        "news_analysis": "",
        "custom_section": "",
        "user_topics": "",
        "portfolio_fit": "",
    }
    current_section: Optional[str] = None
    current_content: List[str] = []
    for line in content.split("\n"):
        upper = line.strip().upper()
        matched = None
        for prefix, key in _SECTION_KEYS:
            if upper.startswith(prefix):
                matched = (prefix, key)
                break
        if matched is not None:
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = matched[1]
            rest = line.split(":", 1)[1].strip() if ":" in line else ""
            current_content = [rest] if rest else []
        elif current_section:
            current_content.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()
    if not any(sections.values()):
        sections["recommendation"] = content
    return sections


def _build_prompt(
    *,
    ticker: str,
    company_name: str,
    user_query: str,
    custom_request: str,
    technical_data: Dict[str, Any],
    risk_metrics: Dict[str, Any],
    news_data: Dict[str, Any],
    news_summary: str,
    portfolio_context: Dict[str, Any],
    omit: Set[str],
    add_list: List[str],
    custom_section_title: Optional[str],
    extra_context: Optional[str] = None,
) -> str:
    data_payload = {
        "technical_data": technical_data,
        "risk_metrics": risk_metrics,
        "news_data": news_data,
        "news_summary": news_summary,
        "portfolio_context": portfolio_context,
    }
    data_summary = json.dumps(data_payload, indent=2, default=str)[:12000]

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
            "any dedicated competitive landscape / competitor benchmarking section"
        )
    omit_instruction = ""
    if omit_lines:
        omit_instruction = (
            "\nOMIT THESE SECTIONS ENTIRELY:\n- " + "\n- ".join(omit_lines)
        )

    add_instruction = ""
    if add_list:
        add_instruction = (
            f"\nADDITIONAL USER-REQUESTED TOPICS: {', '.join(add_list)}.\n"
            "Include a section with header exactly:\nUSER_TOPICS:\n"
            "with 2-4 paragraphs.\n"
        )

    portfolio_prompt = ""
    if portfolio_context and portfolio_context.get("holdings"):
        portfolio_summary = json.dumps(portfolio_context, indent=2, default=str)[:3000]
        portfolio_prompt = f"""

PORTFOLIO_FIT:
The user has an existing portfolio: {portfolio_summary}

Write 2-3 paragraphs analyzing sector diversification, correlation/risk, balance, and position-sizing if adding."""
    else:
        portfolio_prompt = """

PORTFOLIO_FIT:
The user has no portfolio holdings tracked. Write 1 paragraph encouraging them to add holdings in the Portfolio tab."""

    custom_section_prompt = ""
    if custom_section_title and custom_request:
        custom_section_prompt = f"""

CUSTOM_SECTION:
The user requested information about: {custom_request}
Section Title: {custom_section_title}
Write 2-3 detailed paragraphs."""

    extras = f"\n\nADDITIONAL CONTEXT (prior insights):\n{extra_context}" if extra_context else ""

    return f"""You are a senior investment analyst writing a research report for {company_name} ({ticker}).

DATA:
{data_summary}
{extras}

USER REQUEST: {user_query}
{f'SPECIFIC FOCUS: {custom_request}' if custom_request else ''}
{omit_instruction}
{add_instruction}

Write a professional stock research report. Output ONLY plain text paragraphs.

RECOMMENDATION:
2-3 paragraphs. Start with BUY, HOLD, or SELL. Include target price if data supports it.

COMPANY_OVERVIEW:
2-3 paragraphs on what the company does, market position, advantages, products.

FINANCIAL_ANALYSIS:
2-3 paragraphs analyzing revenue, earnings, margins, valuation, balance sheet, cash flow. Use specific numbers.

RISK_ASSESSMENT:
2-3 paragraphs on market, financial, competitive, and governance risks. Reference the supplied risk metrics.

NEWS_ANALYSIS:
1-2 paragraphs on recent news, sentiment, and upcoming catalysts. Reference the supplied news summary.
{custom_section_prompt}{portfolio_prompt}

Format your response EXACTLY with caps headers + colon. Only include headers for sections you actually write.

RECOMMENDATION:
[your paragraphs]

COMPANY_OVERVIEW:
[your paragraphs]

FINANCIAL_ANALYSIS:
[your paragraphs]

RISK_ASSESSMENT:
[your paragraphs]

NEWS_ANALYSIS:
[your paragraphs]
{f'''
CUSTOM_SECTION:
[your paragraphs]
''' if custom_section_title else ''}
{f'''
USER_TOPICS:
[your paragraphs]
''' if add_list else ''}
PORTFOLIO_FIT:
[your paragraphs]"""


async def _fetch_extra_context(
    ticker: str, custom_request: str
) -> Dict[str, Any]:
    if not custom_request:
        return {}
    try:
        return await aget_other(ticker, custom_request)
    except Exception:
        return {}


async def _fetch_prior_insights_context(
    user_query: str,
) -> str:
    """Look up the top-k prior PortfolioInsight rows similar to this query."""
    try:
        from app.db.database import session_scope
        from app.db.repositories import insights as insights_repo
        from app.utils.async_llm import embed_text

        embedding = await embed_text(user_query)
        async with session_scope() as session:
            similar = await insights_repo.find_similar_insights(
                session, embedding=embedding, limit=5
            )
        if not similar:
            return ""
        lines = [
            f"- (sim={row.get('similarity', 0):.2f}) {row.get('insight_text', '')[:300]}"
            for row in similar
        ]
        return "Prior insights from past analyses:\n" + "\n".join(lines)
    except Exception as e:
        logger.debug("prior insights lookup skipped: %s", e)
        return ""


async def _persist_insight(state: ResearchState, sections: Dict[str, str]) -> None:
    """Persist a short, embedding-indexed insight from this run."""
    try:
        from app.db.database import session_scope
        from app.db.repositories import insights as insights_repo
        from app.utils.async_llm import embed_text

        rec = sections.get("recommendation", "")
        rec_short = rec.split("\n")[0][:500] if rec else ""
        if not rec_short:
            return
        ticker = state.get("ticker", "")
        company_name = state.get("company_name", "")
        text = f"{company_name} ({ticker}): {rec_short}"
        embedding = await embed_text(text)
        async with session_scope() as session:
            await insights_repo.create_insight(
                session,
                insight_text=text,
                embedding=embedding,
                portfolio_metadata={
                    "ticker": ticker,
                    "company_name": company_name,
                    "user_query": state.get("user_query", ""),
                },
            )
    except Exception as e:
        logger.debug("persist_insight skipped: %s", e)


@observe(name="compile_report")
async def compile_report(state: ResearchState) -> Dict[str, Any]:
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    user_query = state.get("user_query", "")
    custom_request = state.get("custom_request", "") or ""
    omit = {s.lower() for s in (state.get("omit_sections") or []) if s}
    add_list = [s for s in (state.get("add_sections") or []) if s]

    technical_data = state.get("technical_data", {}) or {}
    risk_metrics = state.get("risk_metrics", {}) or {}
    news_data = state.get("news_data", {}) or {}
    news_summary = state.get("news_summary", "")
    news_reflections = state.get("news_reflections", []) or []
    portfolio_context = state.get("portfolio_context")
    if portfolio_context is None:
        portfolio_context = await get_portfolio_context()

    other_data: Dict[str, Any] = {}
    if custom_request:
        other_data = await _fetch_extra_context(ticker, custom_request)

    custom_section_title, _ = _detect_custom_section_topic(custom_request)
    extra_context = await _fetch_prior_insights_context(user_query) if user_query else ""

    prompt = _build_prompt(
        ticker=ticker,
        company_name=company_name,
        user_query=user_query,
        custom_request=custom_request,
        technical_data=technical_data,
        risk_metrics=risk_metrics,
        news_data=news_data,
        news_summary=news_summary,
        portfolio_context=portfolio_context,
        omit=omit,
        add_list=add_list,
        custom_section_title=custom_section_title,
        extra_context=extra_context,
    )

    response = await chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3500,
        temperature=0.7,
    )
    content = response.get("content", "")
    usage = response.get("usage", {}) or {}
    sections = _parse_sections(content)
    if news_reflections:
        sections_with_meta = dict(sections)
        sections_with_meta["news_reflections"] = news_reflections
    else:
        sections_with_meta = sections
    if custom_section_title:
        sections_with_meta["custom_section_title"] = custom_section_title

    raw_data = {
        "company_info": technical_data.get("company_info", {}),
        "financials": technical_data.get("financials", {}),
        "risks": (risk_metrics or {}).get("raw_risks", {}),
        "news": news_data,
        "portfolio": portfolio_context,
    }
    if other_data:
        raw_data["other"] = other_data

    final_report = {
        "ticker": ticker,
        "company_name": company_name,
        "user_query": user_query,
        "custom_request": custom_request,
        "raw_data": raw_data,
        "analysis": sections_with_meta,
        "portfolio_context": portfolio_context,
        "price_data": state.get("price_data", {}),
    }

    update_current_observation(
        ticker=ticker,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        sections_filled=sum(1 for v in sections.values() if v),
    )

    await _persist_insight(state, sections)

    return {
        "analysis_sections": sections_with_meta,
        "final_report": final_report,
        "token_usage": {
            **(state.get("token_usage", {}) or {}),
            "compile_node": usage.get("total_tokens", 0),
        },
    }
