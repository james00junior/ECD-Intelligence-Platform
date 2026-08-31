"""
Analytics workflow for the ECD intelligence platform.

Responsibilities:

1. Route the question.
2. Build an analytics query plan (LLM or rules).
3. Execute the plan via the analytics agent.
4. Generate a human-readable response.
5. Return a stable workflow state.

Architecture:

    Question
        ↓
    Router
        ↓
    Query Planner
        ↓
    Analytics Agent  (uses planned intent)
        ↓
    Response Generator
        ↓
    Final Answer
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.analytics_agent import analytics_agent
from app.agents.response_generator import generate_response
from app.services.query_planner import create_query_plan
from app.workflows.router import route_question


# -------------------------------------------------------------------
# WORKFLOW STATE
# -------------------------------------------------------------------

class AnalyticsWorkflowState(TypedDict, total=False):
    """State passed between workflow nodes."""

    question: str

    route: str

    intent: str | None

    sql_query: str | None

    results: list[dict[str, Any]]

    answer: str | None

    error: str | None


# -------------------------------------------------------------------
# ROUTER NODE
# -------------------------------------------------------------------

def router_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:
    """Determine which route should handle the question."""

    question = state.get("question", "")

    route = route_question(question)

    return {
        "route": route,
    }


# -------------------------------------------------------------------
# ROUTER DECISION
# -------------------------------------------------------------------

def route_from_router(
    state: AnalyticsWorkflowState,
) -> str:
    """Choose the next workflow node."""

    route = state.get("route")

    if route == "analytics":
        return "analytics"

    return "unknown"


# -------------------------------------------------------------------
# QUERY PLANNER NODE
# -------------------------------------------------------------------

def query_planner_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:
    """Create a structured analytics query plan."""

    question = state.get("question", "")

    plan = create_query_plan(question)

    if plan is None:
        return {
            "intent": None,
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
        }

    return {
        "intent": plan.intent,
        "error": None,
    }


def route_after_query_planner(
    state: AnalyticsWorkflowState,
) -> str:
    """Skip execution when planning failed."""

    if state.get("error") or state.get("intent") is None:
        return "response"

    return "analytics"


# -------------------------------------------------------------------
# ANALYTICS NODE
# -------------------------------------------------------------------

def analytics_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:
    """Execute the analytics agent using the planned intent."""

    question = state.get("question", "")
    intent = state.get("intent")

    result = analytics_agent.invoke(
        {
            "question": question,
            "intent": intent,
        }
    )

    return {
        "intent": result.get("intent"),
        "sql_query": result.get("sql_query"),
        "query": result.get("sql_query"),
        "results": result.get("results", []),
        "error": result.get("error"),
    }


# -------------------------------------------------------------------
# RESPONSE NODE
# -------------------------------------------------------------------

def response_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:
    """Convert structured analytics results into an answer."""

    error = state.get("error")

    if error:
        return {
            "answer": None,
        }

    answer = generate_response(
        intent=state.get("intent"),
        results=state.get("results", []),
    )

    return {
        "answer": answer,
    }


# -------------------------------------------------------------------
# UNKNOWN NODE
# -------------------------------------------------------------------

def unknown_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:
    """Handle questions that are outside the analytics domain."""

    return {
        "error": (
            "No SQL query could be generated "
            "for this question."
        ),
        "intent": None,
        "sql_query": None,
        "results": [],
        "answer": None,
    }


# -------------------------------------------------------------------
# WORKFLOW BUILDER
# -------------------------------------------------------------------

def build_analytics_workflow():
    """Build and compile the analytics workflow."""

    workflow = StateGraph(
        AnalyticsWorkflowState
    )

    # ---------------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------------

    workflow.add_node(
        "router",
        router_node,
    )

    workflow.add_node(
        "query_planner",
        query_planner_node,
    )

    workflow.add_node(
        "analytics",
        analytics_node,
    )

    workflow.add_node(
        "response",
        response_node,
    )

    workflow.add_node(
        "unknown",
        unknown_node,
    )

    # ---------------------------------------------------------------
    # Entry point
    # ---------------------------------------------------------------

    workflow.set_entry_point(
        "router"
    )

    # ---------------------------------------------------------------
    # Router
    # ---------------------------------------------------------------

    workflow.add_conditional_edges(
        "router",
        route_from_router,
        {
            "analytics": "query_planner",
            "unknown": "unknown",
        },
    )

    # ---------------------------------------------------------------
    # Analytics pipeline
    # ---------------------------------------------------------------

    workflow.add_conditional_edges(
        "query_planner",
        route_after_query_planner,
        {
            "analytics": "analytics",
            "response": "response",
        },
    )

    workflow.add_edge(
        "analytics",
        "response",
    )

    workflow.add_edge(
        "response",
        END,
    )

    # ---------------------------------------------------------------
    # Unknown route
    # ---------------------------------------------------------------

    workflow.add_edge(
        "unknown",
        END,
    )

    return workflow.compile()


# -------------------------------------------------------------------
# PUBLIC WORKFLOW
# -------------------------------------------------------------------

analytics_workflow = build_analytics_workflow()


__all__ = [
    "AnalyticsWorkflowState",
    "analytics_workflow",
    "build_analytics_workflow",
]