
from app.agents.analytics_agent import analytics_agent


def initial_state(question: str):

    return {
        "question": question,
        "sql_query": None,
        "results": [],
        "answer": None,
        "error": None,
    }


def test_analytics_agent_count():

    result = analytics_agent.invoke(
        initial_state(
            "count survey responses"
        )
    )

    assert result["sql_query"] is not None
    assert result["results"] is not None
    assert result["answer"] is not None
    assert result["error"] is None


def test_analytics_agent_average_satisfaction():

    result = analytics_agent.invoke(
        initial_state(
            "What is the average satisfaction by country?"
        )
    )

    assert result["sql_query"] is not None
    assert result["results"] is not None
    assert result["answer"] is not None
    assert result["error"] is None


def test_analytics_agent_unknown_question():

    result = analytics_agent.invoke(
        initial_state(
            "What is the weather today?"
        )
    )

    assert result["sql_query"] is None
    assert result["results"] == []
    assert result["error"] is not None
