"""Deterministic source routing for Research Agent questions."""

from __future__ import annotations

from typing import Literal

from app.services.query_planner import create_query_plan


ResearchRoute = Literal[
    "sql",
    "internal_knowledge",
    "sql_and_internal_knowledge",
    "external",
    "direct",
]

INTERNAL_KNOWLEDGE_KEYWORDS = frozenset({
    "document", "documents", "documentation", "policy", "policies",
    "programme guide", "program guide", "report", "reports",
    "knowledge base", "our knowledge", "our latest",
})

EXTERNAL_RESEARCH_KEYWORDS = frozenset({
    "web", "internet", "online", "external", "current regulations",
    "latest regulations", "public research", "industry research",
})


def _contains_keyword(question: str, keywords: frozenset[str]) -> bool:
    return any(keyword in question for keyword in keywords)


def route_research_question(question: str) -> ResearchRoute:
    """Classify the evidence sources required for a question.

    This router makes no provider calls. It uses the existing deterministic
    analytics planner for structured-data detection and explicit phrases for
    internal or external research. External routing is represented now but is
    not executed until RAG-5 adds its controlled tool.
    """

    if not isinstance(question, str) or not question.strip():
        return "direct"

    normalized_question = question.lower().strip()
    needs_sql = create_query_plan(normalized_question) is not None
    needs_internal_knowledge = _contains_keyword(
        normalized_question, INTERNAL_KNOWLEDGE_KEYWORDS
    )
    needs_external_research = _contains_keyword(
        normalized_question, EXTERNAL_RESEARCH_KEYWORDS
    )

    if needs_sql and needs_internal_knowledge:
        return "sql_and_internal_knowledge"
    if needs_sql:
        return "sql"
    if needs_internal_knowledge:
        return "internal_knowledge"
    if needs_external_research:
        return "external"
    return "direct"


def source_requirements_for_route(route: ResearchRoute) -> list[str]:
    """Return source types required by a routed research question."""

    requirements: dict[ResearchRoute, list[str]] = {
        "sql": ["sql"],
        "internal_knowledge": ["internal_document"],
        "sql_and_internal_knowledge": ["sql", "internal_document"],
        "external": ["external"],
        "direct": [],
    }
    return requirements[route]


__all__ = [
    "EXTERNAL_RESEARCH_KEYWORDS",
    "INTERNAL_KNOWLEDGE_KEYWORDS",
    "ResearchRoute",
    "route_research_question",
    "source_requirements_for_route",
]
