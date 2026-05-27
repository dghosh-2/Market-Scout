"""LangGraph scatter-gather DAG: 3 parallel nodes -> compile_report."""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    compile_report,
    get_news_sentiment,
    get_risk_assessment,
    get_technical_analysis,
)
from app.agents.state import ResearchState
from app.telemetry.langfuse_client import observe

logger = logging.getLogger(__name__)

_compiled_graph: Any = None


def _build_graph() -> Any:
    builder = StateGraph(ResearchState)

    builder.add_node("technical", get_technical_analysis)
    builder.add_node("risk", get_risk_assessment)
    builder.add_node("news", get_news_sentiment)
    builder.add_node("compile", compile_report)

    builder.add_edge(START, "technical")
    builder.add_edge(START, "risk")
    builder.add_edge(START, "news")

    builder.add_edge("technical", "compile")
    builder.add_edge("risk", "compile")
    builder.add_edge("news", "compile")

    builder.add_edge("compile", END)

    return builder.compile()


def get_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


@observe(name="research_dag")
async def run_research_graph(initial_state: ResearchState) -> ResearchState:
    """Invoke the compiled DAG and return the merged final state."""
    graph = get_graph()
    final_state: ResearchState = await graph.ainvoke(initial_state)
    return final_state
