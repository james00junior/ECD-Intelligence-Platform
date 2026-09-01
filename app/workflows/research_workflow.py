"""Foundational LangGraph workflow for the Research Agent.

This module deliberately defines the agent's stable contracts before adding
any source-specific behaviour.  Subsequent increments can add SQL, internal
knowledge, and external-research nodes without changing how evidence and
provenance move through the graph.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.database.database import SessionLocal
from app.services.research_router import (
    ResearchRoute,
    route_research_question,
    source_requirements_for_route,
)
from app.tools.internal_knowledge_tool import search_internal_knowledge
from app.tools.sql_research_tool import run_sql_research

EvidenceSourceType = Literal[
    "sql",
    "internal_document",
    "external",
]


class SourceProvenance(TypedDict):
    """Identity and ownership information for one research source."""

    source_type: EvidenceSourceType
    source_id: str
    title: str
    uri: str | None
    organisation_id: int | None
    metadata: dict[str, Any]


class ResearchEvidence(TypedDict):
    """A discrete piece of evidence available to the Research Agent."""

    evidence_id: str
    content: str
    provenance: SourceProvenance
    score: float | None
    metadata: dict[str, Any]


class ResearchState(TypedDict, total=False):
    """State passed between Research Agent nodes.

    ``organisation_id`` is carried on every path so future retrieval nodes
    can enforce tenant boundaries.  Evidence is deliberately structured and
    provenance is embedded in each item, preventing later synthesis work
    from losing source identity.
    """

    question: str
    organisation_id: int | None
    route: ResearchRoute
    source_requirements: list[str]
    evidence: list[ResearchEvidence]
    answer: str | None
    error: str | None
    research_steps: int


def initial_routing_node(
    state: ResearchState,
) -> dict[str, Any]:
    """Determine required sources without making provider calls."""

    route = route_research_question(state.get("question", ""))

    return {
        "route": route,
        "source_requirements": source_requirements_for_route(route),
        "evidence": state.get("evidence", []),
        "research_steps": state.get("research_steps", 0),
        "error": None,
    }


def route_after_initial_routing(state: ResearchState) -> str:
    """Map an evidence route to the first safe research node."""

    route = state.get("route")
    if route in {"sql", "sql_and_internal_knowledge"}:
        return "sql_research"
    if route == "internal_knowledge":
        return "internal_knowledge"
    return "terminal_answer"


def route_after_sql_research(state: ResearchState) -> str:
    """Continue mixed questions into internal retrieval."""

    if state.get("route") == "sql_and_internal_knowledge":
        return "internal_knowledge"
    return "terminal_answer"


def sql_research_node(state: ResearchState) -> dict[str, Any]:
    """Collect SQL evidence through the existing read-only analytics path."""

    result = run_sql_research(
        question=state.get("question", ""),
        organisation_id=state.get("organisation_id"),
    )
    return {
        "evidence": state.get("evidence", []) + result["evidence"],
        "error": result["error"],
        "research_steps": state.get("research_steps", 0) + 1,
    }


def internal_knowledge_node(state: ResearchState) -> dict[str, Any]:
    """Collect organisation-filtered document evidence."""

    organisation_id = state.get("organisation_id")
    if organisation_id is None:
        return {
            "error": "Organisation scope is required for internal research.",
            "research_steps": state.get("research_steps", 0) + 1,
        }

    db = SessionLocal()
    try:
        evidence = search_internal_knowledge(
            question=state.get("question", ""),
            organisation_id=organisation_id,
            db=db,
        )
    except Exception as exc:
        return {
            "error": str(exc),
            "research_steps": state.get("research_steps", 0) + 1,
        }
    finally:
        db.close()

    return {
        "evidence": state.get("evidence", []) + evidence,
        "error": state.get("error"),
        "research_steps": state.get("research_steps", 0) + 1,
    }


def terminal_answer_node(
    state: ResearchState,
) -> dict[str, Any]:
    """Provide the stable terminal state for the foundational graph."""

    return {
        "answer": state.get("answer"),
        "evidence": state.get("evidence", []),
        "error": state.get("error"),
    }


def build_research_workflow():
    """Build a cleanly terminating Research Agent workflow.

    SQL and internal document evidence are collected through existing safety
    boundaries. The terminal node remains the extension point for RAG-6/7
    evidence aggregation and answer synthesis.
    """

    workflow = StateGraph(ResearchState)

    workflow.add_node("initial_routing", initial_routing_node)
    workflow.add_node("sql_research", sql_research_node)
    workflow.add_node("internal_knowledge", internal_knowledge_node)
    workflow.add_node("terminal_answer", terminal_answer_node)

    workflow.set_entry_point("initial_routing")
    workflow.add_conditional_edges(
        "initial_routing",
        route_after_initial_routing,
        {
            "sql_research": "sql_research",
            "internal_knowledge": "internal_knowledge",
            "terminal_answer": "terminal_answer",
        },
    )
    workflow.add_conditional_edges(
        "sql_research",
        route_after_sql_research,
        {
            "internal_knowledge": "internal_knowledge",
            "terminal_answer": "terminal_answer",
        },
    )
    workflow.add_edge("internal_knowledge", "terminal_answer")
    workflow.add_edge("terminal_answer", END)

    return workflow.compile()


research_workflow = build_research_workflow()


__all__ = [
    "EvidenceSourceType",
    "ResearchEvidence",
    "ResearchState",
    "SourceProvenance",
    "build_research_workflow",
    "internal_knowledge_node",
    "initial_routing_node",
    "research_workflow",
    "route_after_initial_routing",
    "route_after_sql_research",
    "sql_research_node",
    "terminal_answer_node",
]
