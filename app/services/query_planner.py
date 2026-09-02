"""
Query planner for the ECD Intelligence Platform.

Responsibilities
----------------
1. Convert a natural-language analytics question into an analytics intent.
2. Produce a structured AnalyticsPlan.
3. Keep planning separate from SQL execution.
4. Provide stable helper functions for workflow integration.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.config.settings import get_settings
from app.models.query_plan import AnalyticsPlan
from app.services.intent_classifier import classify_intent


# ---------------------------------------------------------------------------
# INTENT METADATA
# ---------------------------------------------------------------------------

INTENT_METADATA: dict[str, dict[str, str | None]] = {
    "count_franchisees": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": None,
    },
    "active_franchisees": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": "active",
    },
    "count_children": {
        "entity": "children",
        "measure": "count",
        "dimension": "enrolled",
    },
    "franchisees_in_province": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": "province",
    },
    "franchisees_by_status": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": "status",
    },
    "franchisees_by_province": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": "province",
    },
    "franchisees_by_main_place": {
        "entity": "franchisees",
        "measure": "count",
        "dimension": "main_place",
    },
    "children_by_province": {
        "entity": "children",
        "measure": "count",
        "dimension": "province",
    },
    "population_by_province": {
        "entity": "population",
        "measure": "sum",
        "dimension": "province",
    },
}


VALID_INTENTS = frozenset(INTENT_METADATA)


# ---------------------------------------------------------------------------
# PLAN CREATION
# ---------------------------------------------------------------------------

def plan_from_intent(intent: str) -> AnalyticsPlan:
    metadata = INTENT_METADATA[intent]

    return AnalyticsPlan(
        intent=intent,
        entity=metadata["entity"],
        measure=metadata["measure"],
        dimension=metadata["dimension"],
    )


def build_rule_query_plan(
    question: str,
) -> AnalyticsPlan | None:
    """
    Create an AnalyticsPlan using deterministic intent classification.
    """

    if not isinstance(question, str):
        return None

    question = question.strip()

    if not question:
        return None

    intent = classify_intent(question)

    if intent is None:
        return None

    return plan_from_intent(intent)


def build_query_plan(
    question: str,
) -> AnalyticsPlan | None:
    """
    Create an AnalyticsPlan from a natural-language question.

    Uses the configured planner mode.
    """

    if not isinstance(question, str):
        return None

    question = question.strip()

    if not question:
        return None

    settings = get_settings()

    if settings.query_planner_mode == "llm":
        from app.services.llm_query_planner import (
            build_llm_query_plan,
        )

        plan = build_llm_query_plan(question)

        if plan is not None:
            return plan

    return build_rule_query_plan(question)


def create_query_plan(
    question: str,
) -> AnalyticsPlan | None:
    """
    Public query-plan creation entry point.
    """

    return build_query_plan(question)


def plan_query(
    question: str,
) -> AnalyticsPlan | None:
    """
    Backward-compatible alias.
    """

    return create_query_plan(question)


# ---------------------------------------------------------------------------
# SERIALIZATION
# ---------------------------------------------------------------------------

def plan_to_dict(
    plan: AnalyticsPlan | None,
) -> dict[str, Any] | None:
    """
    Convert an AnalyticsPlan into a plain dictionary.
    """

    if plan is None:
        return None

    return asdict(plan)


def create_query_plan_dict(
    question: str,
) -> dict[str, Any] | None:
    """
    Create and serialize an AnalyticsPlan.
    """

    plan = create_query_plan(question)

    return plan_to_dict(plan)


__all__ = [
    "AnalyticsPlan",
    "INTENT_METADATA",
    "VALID_INTENTS",
    "build_query_plan",
    "build_rule_query_plan",
    "create_query_plan",
    "create_query_plan_dict",
    "plan_from_intent",
    "plan_query",
    "plan_to_dict",
]