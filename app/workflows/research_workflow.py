"""Foundational LangGraph workflow for the Research Agent.

This module deliberately defines the agent's stable contracts before adding
any source-specific behaviour.  Subsequent increments can add SQL, internal
knowledge, and external-research nodes without changing how evidence and
provenance move through the graph.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph


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
    route: str
    evidence: list[ResearchEvidence]
    answer: str | None
    error: str | None
    research_steps: int


PENDING_ROUTE = "pending"


def initial_routing_node(
    state: ResearchState,
) -> dict[str, Any]:
    """Initialise research state before source-routing is introduced.

    RAG-2 replaces the pending route with deterministic source requirements.
    Keeping this node side-effect free ensures the initial graph is safe to
    exercise in tests and does not call any database, embedding, or web
    provider.
    """

    return {
        "route": PENDING_ROUTE,
        "evidence": state.get("evidence", []),
        "research_steps": state.get("research_steps", 0),
        "error": None,
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

    Source routing and retrieval transitions are intentionally added in later
    roadmap increments.  The explicit terminal node makes the initial graph
    executable and establishes the extension point for evidence-aware answer
    synthesis.
    """

    workflow = StateGraph(ResearchState)

    workflow.add_node("initial_routing", initial_routing_node)
    workflow.add_node("terminal_answer", terminal_answer_node)

    workflow.set_entry_point("initial_routing")
    workflow.add_edge("initial_routing", "terminal_answer")
    workflow.add_edge("terminal_answer", END)

    return workflow.compile()


research_workflow = build_research_workflow()


__all__ = [
    "EvidenceSourceType",
    "PENDING_ROUTE",
    "ResearchEvidence",
    "ResearchState",
    "SourceProvenance",
    "build_research_workflow",
    "initial_routing_node",
    "research_workflow",
    "terminal_answer_node",
]
