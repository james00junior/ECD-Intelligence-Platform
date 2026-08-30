
from typing import Any
from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from app.tools.sql_tool import execute_sql


class AgentState(TypedDict):

    question: str

    sql_query: str | None

    results: list[dict[str, Any]]

    answer: str | None

    error: str | None


def generate_sql(
    state: AgentState,
) -> AgentState:
    """
    Generate SQL from the user's question.

    This is intentionally rule-based for now.
    Later, this will be replaced with LLM-based
    text-to-SQL generation.
    """

    question = state["question"].lower()

    sql_query: str | None = None

    if (
        "average satisfaction" in question
        and "country" in question
    ):

        sql_query = """
        SELECT
            country,
            ROUND(
                CAST(
                    AVG(satisfaction_score)
                    AS numeric
                ),
                2
            ) AS average_satisfaction
        FROM survey_responses
        GROUP BY country
        ORDER BY average_satisfaction DESC;
        """

    elif "count" in question:

        sql_query = """
        SELECT
            COUNT(*) AS total_responses
        FROM survey_responses;
        """

    return {
        **state,
        "sql_query": sql_query,
        "error": None,
    }


def run_sql(
    state: AgentState,
) -> AgentState:

    sql_query = state["sql_query"]

    if sql_query is None:

        return {
            **state,
            "results": [],
            "error": "No SQL query could be generated.",
        }

    try:

        results = execute_sql(sql_query)

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


def generate_answer(
    state: AgentState,
) -> AgentState:

    if state["error"]:

        answer = (
            "I could not answer the question. "
            f"Reason: {state['error']}"
        )

    elif not state["results"]:

        answer = (
            "The query executed successfully, "
            "but no results were returned."
        )

    else:

        answer = (
            "Analysis completed successfully. "
            f"Results: {state['results']}"
        )

    return {
        **state,
        "answer": answer,
    }


def build_agent():

    graph = StateGraph(AgentState)

    graph.add_node(
        "generate_sql",
        generate_sql,
    )

    graph.add_node(
        "run_sql",
        run_sql,
    )

    graph.add_node(
        "generate_answer",
        generate_answer,
    )

    graph.add_edge(
        START,
        "generate_sql",
    )

    graph.add_edge(
        "generate_sql",
        "run_sql",
    )

    graph.add_edge(
        "run_sql",
        "generate_answer",
    )

    graph.add_edge(
        "generate_answer",
        END,
    )

    return graph.compile()


analytics_agent = build_agent()
