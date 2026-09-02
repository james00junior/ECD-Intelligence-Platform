"""
Analytics agent for the ECD Intelligence Platform.

Responsibilities:

1. Classify analytics questions.
2. Generate safe SELECT queries.
3. Apply organisation-level data scoping.
4. Execute queries against PostgreSQL.
5. Return a stable structured response.
6. Expose a LangGraph runnable named `analytics_agent`.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.intent_classifier import (
    PROVINCES,
    classify_intent,
)
from app.services.query_planner import build_query_plan
from app.tools.sql_tool import execute_sql


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------

class AnalyticsState(TypedDict, total=False):
    question: str
    organisation_id: int | None

    sql_query: str | None
    sql_parameters: dict[str, Any]

    results: list[dict[str, Any]]

    answer: str | None
    error: str | None

    intent: str | None

    sql_source: str | None
    planner_latency_ms: float | None
    fallback_used: bool | None


# ---------------------------------------------------------------------------
# PROVINCE EXTRACTION
# ---------------------------------------------------------------------------

def extract_province(question: str) -> str | None:
    """
    Extract a South African province from a natural-language question.
    """

    if not isinstance(question, str):
        return None

    normalized = question.lower().strip()

    aliases = {
        "gauteng": "Gauteng",
        "western cape": "Western Cape",
        "eastern cape": "Eastern Cape",
        "kwazulu-natal": "KwaZulu-Natal",
        "kwazulu natal": "KwaZulu-Natal",
        "kzn": "KwaZulu-Natal",
        "free state": "Free State",
        "limpopo": "Limpopo",
        "mpumalanga": "Mpumalanga",
        "north west": "North West",
        "northern cape": "Northern Cape",
    }

    for value in PROVINCES:
        if value in normalized:
            return aliases[value]

    return None


# ---------------------------------------------------------------------------
# SQL GENERATION
# ---------------------------------------------------------------------------

def generate_sql(
    intent: str,
    organisation_id: int | None = None,
    province: str | None = None,
) -> str | None:

    organisation_filter = ""

    if organisation_id is not None:
        organisation_filter = (
            "\nWHERE organisation_id = :organisation_id"
        )

    # ---------------------------------------------------------------
    # TOTAL FRANCHISEES
    # ---------------------------------------------------------------

    if intent == "count_franchisees":

        return f"""
SELECT
    COUNT(*) AS franchisee_count
FROM franchisees
{organisation_filter}
""".strip()

    # ---------------------------------------------------------------
    # ACTIVE FRANCHISEES
    # ---------------------------------------------------------------

    if intent == "active_franchisees":

        if organisation_id is not None:
            return """
SELECT
    COUNT(*) AS active_franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
  AND status = 'ACTIVE'
""".strip()

        return """
SELECT
    COUNT(*) AS active_franchisee_count
FROM franchisees
WHERE status = 'ACTIVE'
""".strip()

    # ---------------------------------------------------------------
    # ENROLLED CHILDREN
    # ---------------------------------------------------------------

    if intent == "count_children":

        if organisation_id is not None:
            return """
SELECT
    COUNT(*) AS child_count
FROM children
WHERE organisation_id = :organisation_id
  AND status = 'ENROLLED'
""".strip()

        return """
SELECT
    COUNT(*) AS child_count
FROM children
WHERE status = 'ENROLLED'
""".strip()

    # ---------------------------------------------------------------
    # FRANCHISEES IN SPECIFIC PROVINCE
    # ---------------------------------------------------------------

    if intent == "franchisees_in_province":

        organisation_conditions = []

        if organisation_id is not None:
            organisation_conditions.append(
                "f.organisation_id = :organisation_id"
            )

        organisation_conditions.append(
            "LOWER(p.name) = LOWER(:province)"
        )

        where_clause = "\nWHERE " + "\n  AND ".join(
            organisation_conditions
        )

        return f"""
SELECT
    p.name AS province,
    COUNT(f.id) AS franchisee_count
FROM franchisees f
JOIN small_areas sa
    ON sa.id = f.small_area_id
JOIN sub_places sp
    ON sp.id = sa.sub_place_id
JOIN main_places mp
    ON mp.id = sp.main_place_id
JOIN local_municipalities lm
    ON lm.id = mp.local_municipality_id
JOIN municipalities m
    ON m.id = lm.municipality_id
JOIN provinces p
    ON p.id = m.province_id
{where_clause}
GROUP BY
    p.id,
    p.name
""".strip()

    # ---------------------------------------------------------------
    # FRANCHISEES BY STATUS
    # ---------------------------------------------------------------

    if intent == "franchisees_by_status":

        if organisation_id is not None:
            return """
SELECT
    status,
    COUNT(*) AS franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
GROUP BY status
ORDER BY status
""".strip()

        return """
SELECT
    status,
    COUNT(*) AS franchisee_count
FROM franchisees
GROUP BY status
ORDER BY status
""".strip()

    # ---------------------------------------------------------------
    # FRANCHISEES BY PROVINCE
    # ---------------------------------------------------------------

    if intent == "franchisees_by_province":

        organisation_condition = ""

        if organisation_id is not None:
            organisation_condition = """
WHERE f.organisation_id = :organisation_id
""".strip()

        return f"""
SELECT
    p.name AS province,
    COUNT(f.id) AS franchisee_count
FROM franchisees f
JOIN small_areas sa
    ON sa.id = f.small_area_id
JOIN sub_places sp
    ON sp.id = sa.sub_place_id
JOIN main_places mp
    ON mp.id = sp.main_place_id
JOIN local_municipalities lm
    ON lm.id = mp.local_municipality_id
JOIN municipalities m
    ON m.id = lm.municipality_id
JOIN provinces p
    ON p.id = m.province_id
{organisation_condition}
GROUP BY
    p.id,
    p.name
ORDER BY
    p.name
""".strip()

    # ---------------------------------------------------------------
    # FRANCHISEES BY MAIN PLACE
    # ---------------------------------------------------------------

    if intent == "franchisees_by_main_place":

        organisation_condition = ""

        if organisation_id is not None:
            organisation_condition = """
WHERE f.organisation_id = :organisation_id
""".strip()

        return f"""
SELECT
    mp.name AS main_place,
    COUNT(f.id) AS franchisee_count
FROM franchisees f
JOIN small_areas sa
    ON sa.id = f.small_area_id
JOIN sub_places sp
    ON sp.id = sa.sub_place_id
JOIN main_places mp
    ON mp.id = sp.main_place_id
{organisation_condition}
GROUP BY
    mp.id,
    mp.name
ORDER BY
    mp.name
""".strip()

    # ---------------------------------------------------------------
    # CHILDREN BY PROVINCE
    # ---------------------------------------------------------------

    if intent == "children_by_province":

        organisation_condition = ""

        if organisation_id is not None:
            organisation_condition = """
  AND c.organisation_id = :organisation_id
""".rstrip()

        return f"""
SELECT
    p.name AS province,
    COUNT(c.id) AS child_count
FROM children c
JOIN small_areas sa
    ON sa.id = c.residential_small_area_id
JOIN sub_places sp
    ON sp.id = sa.sub_place_id
JOIN main_places mp
    ON mp.id = sp.main_place_id
JOIN local_municipalities lm
    ON lm.id = mp.local_municipality_id
JOIN municipalities m
    ON m.id = lm.municipality_id
JOIN provinces p
    ON p.id = m.province_id
WHERE c.status = 'ENROLLED'
{organisation_condition}
GROUP BY
    p.id,
    p.name
ORDER BY
    p.name
""".strip()

    # ---------------------------------------------------------------
    # POPULATION BY PROVINCE
    # ---------------------------------------------------------------

    if intent == "population_by_province":

        return """
SELECT
    p.name AS province,
    SUM(ps.population_total) AS population
FROM population_snapshots ps
JOIN small_areas sa
    ON sa.id = ps.small_area_id
JOIN sub_places sp
    ON sp.id = sa.sub_place_id
JOIN main_places mp
    ON mp.id = sp.main_place_id
JOIN local_municipalities lm
    ON lm.id = mp.local_municipality_id
JOIN municipalities m
    ON m.id = lm.municipality_id
JOIN provinces p
    ON p.id = m.province_id
GROUP BY
    p.id,
    p.name
ORDER BY
    p.name
""".strip()

    return None


# ---------------------------------------------------------------------------
# LANGGRAPH NODES
# ---------------------------------------------------------------------------

def classify_node(
    state: AnalyticsState,
) -> AnalyticsState:

    question = state.get("question", "")
    intent = state.get("intent")

    if intent is None:
        intent = classify_intent(question)

    if intent is None:
        return {
            **state,
            "intent": None,
            "sql_query": None,
            "sql_parameters": {},
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
            "results": [],
        }

    return {
        **state,
        "intent": intent,
        "error": None,
    }


def generate_sql_node(
    state: AnalyticsState,
) -> AnalyticsState:

    existing_sql = state.get("sql_query")

    if existing_sql:
        organisation_id = state.get("organisation_id")
        parameters = dict(
            state.get("sql_parameters") or {}
        )

        if (
            organisation_id is not None
            and ":organisation_id" in existing_sql
        ):
            parameters["organisation_id"] = organisation_id

        return {
            **state,
            "sql_query": existing_sql,
            "sql_parameters": parameters,
            "sql_source": state.get(
                "sql_source"
            ) or "generated",
            "error": None,
        }

    intent = state.get("intent")

    if intent is None:
        return {
            **state,
            "sql_query": None,
            "sql_parameters": {},
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
        }

    organisation_id = state.get("organisation_id")

    province = None

    if intent == "franchisees_in_province":
        province = extract_province(
            state.get("question", "")
        )

        if province is None:
            return {
                **state,
                "sql_query": None,
                "sql_parameters": {},
                "error": (
                    "A province could not be identified "
                    "in the question."
                ),
            }

    query = generate_sql(
        intent=intent,
        organisation_id=organisation_id,
        province=province,
    )

    if query is None:
        return {
            **state,
            "sql_query": None,
            "sql_parameters": {},
            "error": (
                "No SQL query could be generated "
                "for this question."
            ),
        }

    parameters: dict[str, Any] = {}

    if organisation_id is not None:
        parameters["organisation_id"] = organisation_id

    if province is not None:
        parameters["province"] = province

    return {
        **state,
        "sql_query": query,
        "sql_parameters": parameters,
        "sql_source": state.get(
            "sql_source"
        ) or "canned",
        "error": None,
    }


def execute_sql_node(
    state: AnalyticsState,
) -> AnalyticsState:

    query = state.get("sql_query")

    if not query:
        return {
            **state,
            "results": [],
        }

    try:
        from app.tools.sql_tool import validate_sql

        validate_sql(query)

        if state.get("sql_source") in {
            "generated",
            "repaired",
        }:
            from app.services.sql_guard import (
                validate_generated_sql,
            )

            validate_generated_sql(
                query,
                organisation_id=state.get(
                    "organisation_id"
                ),
            )

        results = execute_sql(
            query,
            state.get("sql_parameters", {}),
        )

        return {
            **state,
            "results": results,
            "error": None,
        }

    except Exception as exc:
        return {
            **state,
            "results": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# ROUTING
# ---------------------------------------------------------------------------

def route_after_classification(
    state: AnalyticsState,
) -> str:

    if state.get("intent") is None:
        return "end"

    return "generate_sql"


def route_after_sql_generation(
    state: AnalyticsState,
) -> str:

    if state.get("sql_query") is None:
        return "end"

    return "execute_sql"


# ---------------------------------------------------------------------------
# LANGGRAPH WORKFLOW
# ---------------------------------------------------------------------------

def build_analytics_graph():

    graph = StateGraph(AnalyticsState)

    graph.add_node(
        "classify",
        classify_node,
    )

    graph.add_node(
        "generate_sql",
        generate_sql_node,
    )

    graph.add_node(
        "execute_sql",
        execute_sql_node,
    )

    graph.add_edge(
        START,
        "classify",
    )

    graph.add_conditional_edges(
        "classify",
        route_after_classification,
        {
            "generate_sql": "generate_sql",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "generate_sql",
        route_after_sql_generation,
        {
            "execute_sql": "execute_sql",
            "end": END,
        },
    )

    graph.add_edge(
        "execute_sql",
        END,
    )

    return graph.compile()


analytics_agent = build_analytics_graph()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _error(
    message: str,
    intent: str | None = None,
) -> dict[str, Any]:

    return {
        "intent": intent,
        "query": None,
        "sql_query": None,
        "results": [],
        "error": message,
    }


def _success(
    intent: str,
    query: str,
    results: list[dict[str, Any]],
) -> dict[str, Any]:

    return {
        "intent": intent,
        "query": query,
        "sql_query": query,
        "results": results,
        "error": None,
    }


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTION
# ---------------------------------------------------------------------------

def run_agent(
    question: str,
    organisation_id: int | None = None,
) -> dict[str, Any]:

    if not isinstance(question, str):
        return _error(
            "Question must be a string."
        )

    from app.config.settings import get_settings
    from app.tools.sql_tool import validate_sql

    settings = get_settings()

    sql_source = "canned"
    planner_latency_ms = None
    fallback_used = False

    query = None
    parameters: dict[str, Any] = {}
    intent = None

    plan = build_query_plan(question)

    if plan is not None:
        intent = plan.intent

    if settings.query_planner_mode == "llm":

        from app.services.text_to_sql import (
            generate_select,
        )

        generated = generate_select(
            question,
            organisation_id=organisation_id,
        )

        if generated is not None:

            query = generated.sql
            parameters = dict(
                generated.parameters
            )

            sql_source = generated.source
            planner_latency_ms = (
                generated.latency_ms
            )

            if intent is None:
                intent = "generated_sql"

    if query is None:

        if plan is None:
            return _error(
                "No SQL query could be generated "
                "for this question."
            )

        intent = plan.intent

        province = None

        if intent == "franchisees_in_province":

            province = extract_province(
                question
            )

            if province is None:
                return _error(
                    "A province could not be identified "
                    "in the question.",
                    intent=intent,
                )

            parameters["province"] = province

        query = generate_sql(
            intent=intent,
            organisation_id=organisation_id,
            province=province,
        )

        sql_source = "canned"

        fallback_used = (
            settings.query_planner_mode == "llm"
        )

        if query is None:
            return _error(
                "No SQL query could be generated "
                "for this question.",
                intent=intent,
            )

        if (
            organisation_id is not None
            and ":organisation_id" in query
        ):
            parameters[
                "organisation_id"
            ] = organisation_id

    validate_sql(query)

    try:

        results = execute_sql(
            query,
            parameters,
        )

    except Exception as exc:

        return _error(
            str(exc),
            intent=intent,
        )

    payload = _success(
        intent=intent,
        query=query,
        results=results,
    )

    payload["sql_source"] = sql_source
    payload["planner_latency_ms"] = (
        planner_latency_ms
    )
    payload["fallback_used"] = fallback_used

    return payload


__all__ = [
    "AnalyticsState",
    "analytics_agent",
    "build_analytics_graph",
    "classify_intent",
    "extract_province",
    "generate_sql",
    "run_agent",
]