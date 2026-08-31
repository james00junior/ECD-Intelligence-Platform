"""
Deterministic question router.

This router decides which workflow should handle a user question.
Later, its implementation can be replaced with an LLM router without
changing the overall LangGraph architecture.
"""

from __future__ import annotations


ANALYTICS_ROUTE = "analytics"
UNKNOWN_ROUTE = "unknown"


def route_question(question: str) -> str:
    """
    Route a user question to the appropriate workflow.

    Current routes:
        - analytics
        - unknown
    """

    if not isinstance(question, str):
        return UNKNOWN_ROUTE

    q = question.lower().strip()

    if not q:
        return UNKNOWN_ROUTE

    analytics_keywords = [
        "franchisee",
        "franchisees",
        "child",
        "children",
        "enrolled",
        "population",
        "province",
        "status",
        "main place",
        "municipality",
        "count",
        "how many",
        "total",
    ]

    if any(keyword in q for keyword in analytics_keywords):
        return ANALYTICS_ROUTE

    return UNKNOWN_ROUTE


__all__ = [
    "ANALYTICS_ROUTE",
    "UNKNOWN_ROUTE",
    "route_question",
]
