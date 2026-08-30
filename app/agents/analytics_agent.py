
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

    Phase 1:
        Deterministic rule-based text-to-SQL.

    Later:
        This node will be replaced/enhanced with an
        LLM-based SQL generation and reasoning layer.
    """

    question = state["question"].lower().strip()

    sql_query: str | None = None

    # ---------------------------------------------------------
    # COUNT FRANCHISEES
    # ---------------------------------------------------------

    if (
        "how many franchisees" in question
        and "by status" not in question
    ):

        sql_query = """
        SELECT
            COUNT(*) AS total_franchisees
        FROM franchisees;
        """

    # ---------------------------------------------------------
    # ACTIVE FRANCHISEES
    # ---------------------------------------------------------

    elif (
        "active franchisees" in question
        or (
            "franchisees" in question
            and "active" in question
        )
    ):

        sql_query = """
        SELECT
            COUNT(*) AS active_franchisees
        FROM franchisees
        WHERE status = 'ACTIVE';
        """

    # ---------------------------------------------------------
    # INACTIVE FRANCHISEES
    # ---------------------------------------------------------

    elif (
        "inactive franchisees" in question
        or (
            "franchisees" in question
            and "inactive" in question
        )
    ):

        sql_query = """
        SELECT
            COUNT(*) AS inactive_franchisees
        FROM franchisees
        WHERE status = 'INACTIVE';
        """

    # ---------------------------------------------------------
    # COUNT CHILDREN
    # ---------------------------------------------------------

    elif (
        "how many children" in question
        or "number of children" in question
        or "children are enrolled" in question
    ):

        sql_query = """
        SELECT
            COUNT(*) AS total_children
        FROM children
        WHERE status = 'ENROLLED';
        """

    # ---------------------------------------------------------
    # FRANCHISEES BY STATUS
    # ---------------------------------------------------------

    elif (
        "franchisees by status" in question
        or (
            "franchisees" in question
            and "status" in question
        )
    ):

        sql_query = """
        SELECT
            status,
            COUNT(*) AS franchisee_count
        FROM franchisees
        GROUP BY status
        ORDER BY status;
        """

    return {
        **state,
        "sql_query": sql_query,
        "error": None,
    }


def run_sql(
    state: AgentState,
) -> AgentState:
    """
    Execute the generated SQL using the read-only SQL tool.
    """

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
    """
    Convert SQL results into a simple human-readable answer.

    This is intentionally simple in Phase 1.

    Later this node will use an LLM to produce richer,
    context-aware analytical explanations.
    """

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
    """
    Build and compile the analytics LangGraph workflow.

    Current workflow:

        START
          ↓
      generate_sql
          ↓
        run_sql
          ↓
    generate_answer
          ↓
         END
    """

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
