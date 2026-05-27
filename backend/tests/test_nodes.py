"""Unit tests for individual graph nodes."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import sys

import app.agents.nodes.news_sentiment as news_mod  # noqa: E402
import app.agents.nodes.risk_assessment as risk_mod  # noqa: E402
import app.agents.nodes.technical_analysis as tech_mod  # noqa: E402

# nodes/__init__.py re-exports the `compile_report` function with the same
# name as the submodule, shadowing it. Resolve to the submodule via sys.modules.
import app.agents.nodes.compile_report  # noqa: E402,F401
cr_mod = sys.modules["app.agents.nodes.compile_report"]
from app.agents.nodes.compile_report import compile_report as compile_report_fn  # noqa: E402


@pytest.mark.asyncio
async def test_technical_analysis_aggregates_yfinance(monkeypatch):
    monkeypatch.setattr(tech_mod, "aget_company_info", AsyncMock(return_value={"name": "Apple"}))
    monkeypatch.setattr(tech_mod, "aget_financials", AsyncMock(return_value={"current_price": 200}))
    monkeypatch.setattr(
        tech_mod, "aget_price_history",
        AsyncMock(return_value={"prices": [{"close": 200}], "change_percent": 1.5}),
    )

    result = await tech_mod.get_technical_analysis({"ticker": "AAPL"})

    assert result["technical_data"]["company_info"]["name"] == "Apple"
    assert result["technical_data"]["financials"]["current_price"] == 200
    assert result["price_data"]["change_percent"] == 1.5


@pytest.mark.asyncio
async def test_risk_assessment_computes_portfolio_metrics(monkeypatch):
    monkeypatch.setattr(
        risk_mod, "aget_risks",
        AsyncMock(return_value={
            "beta": 1.4, "volatility_percent": 25, "debt_to_equity": 1.2,
            "current_ratio": 1.0, "short_percent_of_float": 0.02, "overall_risk": 5,
        }),
    )
    monkeypatch.setattr(
        risk_mod, "get_portfolio_context",
        AsyncMock(return_value={
            "holdings": [
                {"ticker": "MSFT", "weight": 60.0, "beta": 0.9},
                {"ticker": "TSLA", "weight": 40.0, "beta": 2.0},
            ]
        }),
    )

    out = await risk_mod.get_risk_assessment({"ticker": "AAPL"})
    metrics = out["risk_metrics"]
    assert metrics["ticker_beta"] == 1.4
    # Weighted beta = (60*0.9 + 40*2.0) / 100 = 1.34
    assert metrics["portfolio_weighted_beta_before"] == pytest.approx(1.34, abs=0.01)


@pytest.mark.asyncio
async def test_news_sentiment_parses_summary_and_reflections(monkeypatch):
    fake_news = {
        "articles": [
            {"title": "Apple beats earnings expectations", "publisher": "WSJ"},
            {"title": "Apple supply chain delays", "publisher": "Reuters"},
        ]
    }
    monkeypatch.setattr(news_mod, "aget_news", AsyncMock(return_value=fake_news))
    monkeypatch.setattr(news_mod, "chat_completion", AsyncMock(return_value={
        "content": (
            "SUMMARY:\nApple posted strong earnings but supply remains tight.\n"
            "REFLECTIONS:\n"
            "HEADLINE: Apple beats earnings expectations\n"
            "REFLECTION: Positive for short-term sentiment.\n"
            "HEADLINE: Apple supply chain delays\n"
            "REFLECTION: Drag on near-term revenue.\n"
        ),
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "model": "gpt-4o-mini",
    }))

    out = await news_mod.get_news_sentiment({"ticker": "AAPL", "company_name": "Apple Inc."})
    assert "Apple posted strong earnings" in out["news_summary"]
    assert len(out["news_reflections"]) == 2
    assert out["news_reflections"][0]["reflection"] == "Positive for short-term sentiment."
    assert out["token_usage"]["news_node"] == 30


@pytest.mark.asyncio
async def test_compile_report_parses_sections_and_returns_final_report(monkeypatch):
    monkeypatch.setattr(cr_mod, "chat_completion", AsyncMock(return_value={
        "content": (
            "RECOMMENDATION:\nBUY — strong fundamentals.\n\n"
            "COMPANY_OVERVIEW:\nApple makes consumer tech.\n\n"
            "FINANCIAL_ANALYSIS:\nMargins healthy.\n\n"
            "RISK_ASSESSMENT:\nManageable.\n\n"
            "NEWS_ANALYSIS:\nPositive sentiment.\n\n"
            "PORTFOLIO_FIT:\nFits well.\n"
        ),
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        "model": "gpt-4o-mini",
    }))
    monkeypatch.setattr(cr_mod, "_fetch_extra_context", AsyncMock(return_value={}))
    monkeypatch.setattr(cr_mod, "_fetch_prior_insights_context", AsyncMock(return_value=""))
    monkeypatch.setattr(cr_mod, "_persist_insight", AsyncMock(return_value=None))
    monkeypatch.setattr(cr_mod, "get_portfolio_context", AsyncMock(return_value={"holdings": []}))

    state = {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "user_query": "Analyze Apple",
        "custom_request": "",
        "omit_sections": [],
        "add_sections": [],
        "technical_data": {"company_info": {}, "financials": {}},
        "risk_metrics": {"raw_risks": {}},
        "news_data": {"articles": []},
        "news_summary": "",
        "news_reflections": [],
        "portfolio_context": {"holdings": []},
        "price_data": {},
    }
    out = await compile_report_fn(state)
    sections = out["analysis_sections"]
    assert sections["recommendation"].startswith("BUY")
    assert sections["company_overview"].startswith("Apple makes")
    assert out["final_report"]["ticker"] == "AAPL"
    assert out["final_report"]["analysis"]["portfolio_fit"].startswith("Fits well")
