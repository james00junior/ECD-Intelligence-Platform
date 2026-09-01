"""
Analytics workflow for the ECD Intelligence Platform.

Responsibilities:

1. Route the question.
2. Build an analytics query plan.
3. Execute the plan through the analytics agent.
4. Generate a human-readable response.
5. Preserve organisation scope throughout the workflow.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.analytics_agent import analytics_agent
from app.agents.response_generator import generate_response
from app.services.query_planner import create_query_plan
from app.workflows.router import route_question


class AnalyticsWorkflowState(TypedDict, total=False):

    question: str

    organisation_id: int | None

    route: str

    intent: str | None

    sql_query: str | None

    query: str | None

    results: list[dict[str, Any]]

    answer: str | None

    error: str | None


def router_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

    question = state.get("question", "")

    route = route_question(question)

    return {
        "route": route,
    }


def route_from_router(
    state: AnalyticsWorkflowState,
) -> str:

    route = state.get("route")

    if route == "analytics":
        return "analytics"

    return "unknown"


def query_planner_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

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

    if state.get("error") or state.get("intent") is None:
        return "response"

    return "analytics"


def analytics_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

    question = state.get("question", "")
    intent = state.get("intent")
    organisation_id = state.get("organisation_id")

    result = analytics_agent.invoke(
        {
            "question": question,
            "intent": intent,
            "organisation_id": organisation_id,
        }
    )

    return {
        "intent": result.get("intent"),
        "sql_query": result.get("sql_query"),
        "query": result.get("query"),
        "results": result.get("results", []),
        "error": result.get("error"),
    }


def response_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

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


def unknown_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

    return {
        "error": (
            "No SQL query could be generated "
            "for this question."
        ),
        "intent": None,
        "sql_query": None,
        "query": None,
        "results": [],
        "answer": None,
    }


def build_analytics_workflow():

    workflow = StateGraph(
        AnalyticsWorkflowState
    )

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

    workflow.set_entry_point(
        "router"
    )

    workflow.add_conditional_edges(
        "router",
        route_from_router,
        {
            "analytics": "query_planner",
            "unknown": "unknown",
        },
    )

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

    workflow.add_edge(
        "unknown",
        END,
    )

    return workflow.compile()


analytics_workflow = build_analytics_workflow()


__all__ = [
    "AnalyticsWorkflowState",
    "analytics_workflow",
    "build_analytics_workflow",
]