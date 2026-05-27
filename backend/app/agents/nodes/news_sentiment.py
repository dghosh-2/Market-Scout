"""Parallel node: fetch news + summarize sentiment with AsyncOpenAI."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.agents.state import ResearchState
from app.agents.tools import aget_news
from app.telemetry.langfuse_client import observe, update_current_observation
from app.utils.async_llm import chat_completion

logger = logging.getLogger(__name__)


async def _summarize_news(
    ticker: str, company_name: str, articles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    if not articles:
        return {"summary": "", "reflections": [], "usage": {}}

    headlines = "\n".join(
        f"- {a.get('title', '')} ({a.get('publisher', '')})"
        for a in articles
        if a.get("title")
    )
    if not headlines:
        return {"summary": "", "reflections": [], "usage": {}}

    prompt = f"""You are summarizing recent financial news for {company_name} ({ticker}).
Headlines:
{headlines}

Output exactly two blocks:

SUMMARY:
[2-3 sentence overall sentiment summary]

REFLECTIONS:
HEADLINE: [exact headline]
REFLECTION: [1-2 sentence impact analysis]
(repeat for each headline)
"""

    response = await chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.6,
    )

    content = response["content"]
    summary = ""
    reflections: List[Dict[str, str]] = []

    current_headline: str = ""
    current_reflection: str = ""
    in_reflections = False

    for raw in content.split("\n"):
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip() if ":" in line else ""
            in_reflections = False
            continue
        if upper.startswith("REFLECTIONS"):
            in_reflections = True
            continue
        if not in_reflections:
            if line:
                summary = (summary + " " + line).strip() if summary else line
            continue
        if upper.startswith("HEADLINE:"):
            if current_headline and current_reflection:
                reflections.append({
                    "headline": current_headline,
                    "reflection": current_reflection,
                })
            current_headline = line.split(":", 1)[1].strip()
            current_reflection = ""
        elif upper.startswith("REFLECTION:"):
            current_reflection = line.split(":", 1)[1].strip()

    if current_headline and current_reflection:
        reflections.append({
            "headline": current_headline,
            "reflection": current_reflection,
        })

    enriched: List[Dict[str, str]] = []
    for article in articles:
        matched = ""
        title = article.get("title", "")
        if title:
            title_words = set(title.lower().split()[:5])
            for ref in reflections:
                ref_words = set(ref["headline"].lower().split()[:5])
                if len(title_words & ref_words) >= 2:
                    matched = ref["reflection"]
                    break
        enriched.append({
            "title": title,
            "publisher": article.get("publisher", ""),
            "published": article.get("published", ""),
            "reflection": matched
            or "Monitor this development for potential impact on stock performance.",
        })

    return {"summary": summary, "reflections": enriched, "usage": response.get("usage", {})}


@observe(name="get_news_sentiment")
async def get_news_sentiment(state: ResearchState) -> Dict[str, Any]:
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    if not ticker:
        return {"errors": ["news_sentiment: missing ticker"], "news_data": {}, "news_summary": ""}

    try:
        news = await aget_news(ticker)
    except Exception as e:
        logger.exception("news_sentiment yfinance fetch failed for %s", ticker)
        return {"errors": [f"news_sentiment: {e}"], "news_data": {}, "news_summary": ""}

    articles = (news or {}).get("articles", []) if isinstance(news, dict) else []
    summary_payload = await _summarize_news(ticker, company_name, articles[:5])

    usage = summary_payload.get("usage", {}) or {}
    update_current_observation(
        ticker=ticker,
        article_count=len(articles),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )

    return {
        "news_data": news,
        "news_summary": summary_payload.get("summary", ""),
        "news_reflections": summary_payload.get("reflections", []),
        "token_usage": {"news_node": usage.get("total_tokens", 0)},
    }
