"""LangGraph DAG: nodes execute in parallel and converge into compile_report."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents import graph as graph_mod
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_graph_runs_all_nodes_and_compiles(monkeypatch):
    calls: dict = {}

    async def fake_technical(state):
        calls["technical"] = True
        return {
            "technical_data": {
                "company_info": {"name": "Apple Inc.", "sector": "Tech"},
                "financials": {"current_price": 200.0},
            },
            "price_data": {"prices": [{"close": 200.0}], "change_percent": 5.0},
        }

    async def fake_risk(state):
        calls["risk"] = True
        return {"risk_metrics": {"ticker_beta": 1.2}, "portfolio_context": {"holdings": []}}

    async def fake_news(state):
        calls["news"] = True
        return {"news_data": {"articles": []}, "news_summary": "ok", "news_reflections": []}

    async def fake_compile(state):
        calls["compile"] = True
        assert state.get("technical_data") is not None
        assert state.get("risk_metrics") is not None
        assert state.get("news_data") is not None
        return {
            "analysis_sections": {"recommendation": "BUY"},
            "final_report": {
                "ticker": state["ticker"],
                "company_name": state["company_name"],
                "analysis": {"recommendation": "BUY"},
                "raw_data": {},
                "portfolio_context": {},
                "price_data": state.get("price_data", {}),
            },
        }

    from app.agents import nodes as nodes_mod

    monkeypatch.setattr(nodes_mod, "get_technical_analysis", fake_technical)
    monkeypatch.setattr(nodes_mod, "get_risk_assessment", fake_risk)
    monkeypatch.setattr(nodes_mod, "get_news_sentiment", fake_news)
    monkeypatch.setattr(nodes_mod, "compile_report", fake_compile)
    monkeypatch.setattr(graph_mod, "get_technical_analysis", fake_technical)
    monkeypatch.setattr(graph_mod, "get_risk_assessment", fake_risk)
    monkeypatch.setattr(graph_mod, "get_news_sentiment", fake_news)
    monkeypatch.setattr(graph_mod, "compile_report", fake_compile)
    monkeypatch.setattr(graph_mod, "_compiled_graph", None)

    initial: ResearchState = {
        "user_query": "Analyze Apple",
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
    }
    final_state = await graph_mod.run_research_graph(initial)

    assert calls == {"technical": True, "risk": True, "news": True, "compile": True}
    assert final_state["final_report"]["ticker"] == "AAPL"
    assert final_state["analysis_sections"]["recommendation"] == "BUY"
