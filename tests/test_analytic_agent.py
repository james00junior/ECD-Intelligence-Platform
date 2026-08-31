from app.agents.analytics_agent import analytics_agent


def run_agent(question: str):
    return analytics_agent.invoke(
        {
            "question": question,
            "sql_query": None,
            "results": [],
            "answer": None,
            "error": None,
            "intent": None,
        }
    )


def test_analytics_agent_count():
    result = run_agent(
        "How many franchisees are there?"
    )

    assert result["error"] is None
    assert result["intent"] == "count_franchisees"
    assert result["results"]
    assert "franchisee_count" in result["results"][0]


def test_analytics_agent_active_franchisees():
    result = run_agent(
        "How many active franchisees are there?"
    )

    assert result["error"] is None
    assert result["intent"] == "active_franchisees"
    assert result["results"]
    assert "active_franchisee_count" in result["results"][0]


def test_analytics_agent_children():
    result = run_agent(
        "How many children are enrolled?"
    )

    assert result["error"] is None
    assert result["intent"] == "count_children"
    assert result["results"]
    assert "child_count" in result["results"][0]


def test_analytics_agent_franchisees_by_status():
    result = run_agent(
        "How many franchisees are there by status?"
    )

    assert result["error"] is None
    assert result["intent"] == "franchisees_by_status"
    assert result["results"]
    assert "status" in result["results"][0]
    assert "franchisee_count" in result["results"][0]


def test_analytics_agent_unknown_question():
    result = run_agent(
        "What is the weather in Johannesburg?"
    )

    assert (
        result["error"]
        == "No SQL query could be generated for this question."
    )

    assert result["results"] == []


def test_analytics_agent_franchisees_by_province():
    result = run_agent(
        "How many franchisees are there by province?"
    )

    assert result["error"] is None
    assert result["intent"] == "franchisees_by_province"
    assert result["results"]
    assert "province" in result["results"][0]
    assert "franchisee_count" in result["results"][0]


def test_analytics_agent_franchisees_by_main_place():
    result = run_agent(
        "How many franchisees are there by main place?"
    )

    assert result["error"] is None
    assert result["intent"] == "franchisees_by_main_place"
    assert result["results"]
    assert "main_place" in result["results"][0]
    assert "franchisee_count" in result["results"][0]


def test_analytics_agent_children_by_province():
    result = run_agent(
        "How many enrolled children are there by province?"
    )

    assert result["error"] is None
    assert result["intent"] == "children_by_province"
    assert result["results"]
    assert "province" in result["results"][0]
    assert "child_count" in result["results"][0]


def test_analytics_agent_population_by_province():
    result = run_agent(
        "What is the population by province?"
    )

    assert result["error"] is None
    assert result["intent"] == "population_by_province"
    assert result["results"]
    assert "province" in result["results"][0]
    assert "population" in result["results"][0]


def test_analytics_agent_uses_preplanned_intent(monkeypatch):
    monkeypatch.setattr(
        "app.agents.analytics_agent.classify_intent",
        lambda question: "count_franchisees",
    )

    result = analytics_agent.invoke(
        {
            "question": (
                "How many enrolled children are there by province?"
            ),
            "intent": "children_by_province",
        }
    )

    assert result["error"] is None
    assert result["intent"] == "children_by_province"
    assert result["results"]
    assert "province" in result["results"][0]
    assert "child_count" in result["results"][0]
