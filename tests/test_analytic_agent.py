
from app.agents.analytics_agent import analytics_agent


def run_agent(question: str):
    """Run the analytics agent with a standard initial state."""

    return analytics_agent.invoke(
        {
            "question": question,
            "sql_query": None,
            "results": [],
            "answer": None,
            "error": None,
        }
    )


def test_analytics_agent_count():
    """The agent should count franchisees."""

    result = run_agent(
        "How many franchisees are there?"
    )

    assert result["error"] is None
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        "COUNT" in result["sql_query"].upper()
    )

    assert (
        "FRANCHISEES" in result["sql_query"].upper()
    )


def test_analytics_agent_active_franchisees():
    """The agent should count active franchisees."""

    result = run_agent(
        "How many active franchisees are there?"
    )

    assert result["error"] is None
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        "ACTIVE" in result["sql_query"].upper()
    )

    assert (
        "FRANCHISEES" in result["sql_query"].upper()
    )


def test_analytics_agent_children():
    """The agent should count enrolled children."""

    result = run_agent(
        "How many children are enrolled?"
    )

    assert result["error"] is None
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        "CHILDREN" in result["sql_query"].upper()
    )


def test_analytics_agent_franchisees_by_status():
    """The agent should analyse franchisees by status."""

    result = run_agent(
        "How many franchisees are there by status?"
    )

    assert result["error"] is None
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        "GROUP BY" in result["sql_query"].upper()
    )

    assert (
        "STATUS" in result["sql_query"].upper()
    )
