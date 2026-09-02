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
from app.services.query_planner import build_rule_query_plan
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

    sql_source: str | None

    sql_parameters: dict[str, Any]

    planner_latency_ms: float | None

    fallback_used: bool | None


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

    from app.config.settings import get_settings

    question = state.get("question", "")
    organisation_id = state.get("organisation_id")
    settings = get_settings()

    rule_plan = build_rule_query_plan(question)

    if settings.query_planner_mode == "llm":
        from app.services.text_to_sql import generate_select

        generated = generate_select(
            question,
            organisation_id=organisation_id,
        )
        if generated is not None:
            return {
                "intent": rule_plan.intent if rule_plan is not None else "generated_sql",
                "sql_query": generated.sql,
                "sql_parameters": generated.parameters,
                "sql_source": generated.source,
                "planner_latency_ms": generated.latency_ms,
                "fallback_used": False,
                "error": None,
            }

        if rule_plan is not None:
            return {
                "intent": rule_plan.intent,
                "sql_query": None,
                "sql_source": "canned",
                "fallback_used": True,
                "error": None,
            }

        return {
            "intent": None,
            "sql_query": None,
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
        }

    if rule_plan is None:
        return {
            "intent": None,
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
        }

    return {
        "intent": rule_plan.intent,
        "sql_source": "canned",
        "fallback_used": False,
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
            "sql_query": state.get("sql_query"),
            "sql_parameters": state.get("sql_parameters") or {},
            "sql_source": state.get("sql_source"),
        }
    )

    return {
        "intent": result.get("intent"),
        "sql_query": result.get("sql_query"),
        "query": result.get("query") or result.get("sql_query"),
        "results": result.get("results", []),
        "error": result.get("error"),
        "sql_source": result.get("sql_source") or state.get("sql_source"),
        "planner_latency_ms": result.get("planner_latency_ms")
        or state.get("planner_latency_ms"),
        "fallback_used": result.get("fallback_used")
        if result.get("fallback_used") is not None
        else state.get("fallback_used"),
    }


def response_node(
    state: AnalyticsWorkflowState,
) -> dict[str, Any]:

    error = state.get("error")

    if error:
        return {
            "answer": None,
        }

    from app.services.result_interpreter import interpret_results

    answer = interpret_results(
        question=state.get("question", ""),
        results=state.get("results", []),
        intent=state.get("intent"),
        sql_source=state.get("sql_source") or "canned",
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