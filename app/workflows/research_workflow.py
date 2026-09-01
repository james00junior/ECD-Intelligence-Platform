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
from app.services.evidence_aggregation import aggregate_evidence
from app.services.grounded_synthesis import synthesize_grounded_answer
from app.services.research_loop import (
    DEFAULT_MAX_RESEARCH_STEPS,
    evaluate_evidence_sufficiency,
    refine_research_query,
)
from app.services.research_router import (
    ResearchRoute,
    route_research_question,
    source_requirements_for_route,
)
from app.tools.internal_knowledge_tool import search_internal_knowledge
from app.tools.external_research_tool import search_external_research
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
    selected_evidence: list[ResearchEvidence]
    rejected_evidence: list[ResearchEvidence]
    conflicts: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    answer: str | None
    error: str | None
    research_steps: int
    research_attempts: int
    max_research_steps: int
    research_query: str
    retry_requested: bool
    sufficiency_reason: str | None


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
        "research_attempts": state.get("research_attempts", 0),
        "max_research_steps": state.get("max_research_steps", DEFAULT_MAX_RESEARCH_STEPS),
        "research_query": state.get("research_query", state.get("question", "")),
        "retry_requested": False,
        "error": None,
    }


def route_after_initial_routing(state: ResearchState) -> str:
    """Map an evidence route to the first safe research node."""

    route = state.get("route")
    requirements = state.get("source_requirements", [])
    if "sql" in requirements:
        return "sql_research"
    if "internal_document" in requirements:
        return "internal_knowledge"
    if "external" in requirements:
        return "external_research"
    return "aggregate_evidence"


def route_after_sql_research(state: ResearchState) -> str:
    """Continue mixed questions into internal retrieval."""

    requirements = state.get("source_requirements", [])
    if "internal_document" in requirements:
        return "internal_knowledge"
    if "external" in requirements:
        return "external_research"
    return "aggregate_evidence"


def route_after_internal_knowledge(state: ResearchState) -> str:
    if "external" in state.get("source_requirements", []):
        return "external_research"
    return "aggregate_evidence"


def sql_research_node(state: ResearchState) -> dict[str, Any]:
    """Collect SQL evidence through the existing read-only analytics path."""

    result = run_sql_research(
        question=state.get("research_query", state.get("question", "")),
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
            question=state.get("research_query", state.get("question", "")),
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


def external_research_node(state: ResearchState) -> dict[str, Any]:
    """Collect public evidence without passing organisation data to the web."""

    result = search_external_research(
        state.get("research_query", state.get("question", ""))
    )
    return {
        "evidence": state.get("evidence", []) + result["evidence"],
        "error": state.get("error") or result["error"],
        "research_steps": state.get("research_steps", 0) + 1,
    }


def aggregate_evidence_node(state: ResearchState) -> dict[str, Any]:
    """Select tenant-safe evidence and preserve any detected conflicts."""

    result = aggregate_evidence(
        evidence_items=state.get("evidence", []),
        organisation_id=state.get("organisation_id"),
    )
    return result


def research_loop_node(state: ResearchState) -> dict[str, Any]:
    """Evaluate evidence and prepare one bounded, refined follow-up pass."""

    decision = evaluate_evidence_sufficiency(
        evidence=state.get("selected_evidence", []),
        conflicts=state.get("conflicts", []),
        error=state.get("error"),
        research_steps=state.get("research_steps", 0),
        max_research_steps=state.get("max_research_steps", DEFAULT_MAX_RESEARCH_STEPS),
        has_retrieval_source=bool(state.get("source_requirements", [])),
    )
    if not decision["should_retry"]:
        return {
            "retry_requested": False,
            "sufficiency_reason": decision["reason"],
            "error": state.get("error") or (
                None if decision["sufficient"] else decision["reason"]
            ),
        }

    attempts = state.get("research_attempts", 0) + 1
    return {
        "retry_requested": True,
        "research_attempts": attempts,
        "research_query": refine_research_query(
            state.get("question", ""), attempts
        ),
        "sufficiency_reason": decision["reason"],
    }


def route_after_research_loop(state: ResearchState) -> str:
    """Continue a bounded retry or synthesize the final evidence state."""

    if not state.get("retry_requested"):
        return "synthesis"
    return route_after_initial_routing(state)


def synthesis_node(state: ResearchState) -> dict[str, Any]:
    """Create a grounded answer from selected evidence only."""

    result = synthesize_grounded_answer(
        question=state.get("question", ""),
        evidence=state.get("selected_evidence", []),
    )
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "error": state.get("error") or result["error"],
    }


def terminal_answer_node(
    state: ResearchState,
) -> dict[str, Any]:
    """Return the answer, selected evidence, and citations to the caller."""

    return {
        "answer": state.get("answer"),
        "evidence": state.get("evidence", []),
        "selected_evidence": state.get("selected_evidence", []),
        "citations": state.get("citations", []),
        "error": state.get("error"),
    }


def build_research_workflow():
    """Build a cleanly terminating Research Agent workflow.

    SQL, internal-document, and external research nodes feed a tenant-safe
    aggregation step and a bounded retry decision before grounded synthesis.
    """

    workflow = StateGraph(ResearchState)

    workflow.add_node("initial_routing", initial_routing_node)
    workflow.add_node("sql_research", sql_research_node)
    workflow.add_node("internal_knowledge", internal_knowledge_node)
    workflow.add_node("external_research", external_research_node)
    workflow.add_node("aggregate_evidence", aggregate_evidence_node)
    workflow.add_node("research_loop", research_loop_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("terminal_answer", terminal_answer_node)

    workflow.set_entry_point("initial_routing")
    workflow.add_conditional_edges(
        "initial_routing",
        route_after_initial_routing,
        {
            "sql_research": "sql_research",
            "internal_knowledge": "internal_knowledge",
            "external_research": "external_research",
            "aggregate_evidence": "aggregate_evidence",
        },
    )
    workflow.add_conditional_edges(
        "sql_research",
        route_after_sql_research,
        {
            "internal_knowledge": "internal_knowledge",
            "external_research": "external_research",
            "aggregate_evidence": "aggregate_evidence",
        },
    )
    workflow.add_conditional_edges(
        "internal_knowledge",
        route_after_internal_knowledge,
        {
            "external_research": "external_research",
            "aggregate_evidence": "aggregate_evidence",
        },
    )
    workflow.add_edge("external_research", "aggregate_evidence")
    workflow.add_edge("aggregate_evidence", "research_loop")
    workflow.add_conditional_edges(
        "research_loop",
        route_after_research_loop,
        {
            "sql_research": "sql_research",
            "internal_knowledge": "internal_knowledge",
            "external_research": "external_research",
            "aggregate_evidence": "aggregate_evidence",
            "synthesis": "synthesis",
        },
    )
    workflow.add_edge("synthesis", "terminal_answer")
    workflow.add_edge("terminal_answer", END)

    return workflow.compile()


research_workflow = build_research_workflow()


__all__ = [
    "EvidenceSourceType",
    "ResearchEvidence",
    "ResearchState",
    "SourceProvenance",
    "build_research_workflow",
    "aggregate_evidence_node",
    "external_research_node",
    "internal_knowledge_node",
    "initial_routing_node",
    "research_workflow",
    "route_after_initial_routing",
    "route_after_sql_research",
    "route_after_internal_knowledge",
    "route_after_research_loop",
    "research_loop_node",
    "synthesis_node",
    "sql_research_node",
    "terminal_answer_node",
]
