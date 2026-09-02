from app.agents.analytics_agent import generate_sql_node
from app.config.settings import get_settings
from app.workflows.analytics_workflow import query_planner_node


VALID_SQL = """
SELECT COUNT(*) AS franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
"""


def test_generate_sql_node_reuses_validated_generated_sql():
    state = generate_sql_node(
        {
            "question": "How many franchisees are there?",
            "organisation_id": 1,
            "intent": "generated_sql",
            "sql_query": VALID_SQL.strip(),
            "sql_parameters": {"organisation_id": 1},
            "sql_source": "generated",
        }
    )
    assert state["error"] is None
    assert state["sql_source"] == "generated"
    assert ":organisation_id" in state["sql_query"]
    assert state["sql_parameters"]["organisation_id"] == 1


def test_generate_sql_node_falls_back_to_canned_intent_sql():
    state = generate_sql_node(
        {
            "question": "How many franchisees are there?",
            "organisation_id": 1,
            "intent": "count_franchisees",
        }
    )
    assert state["error"] is None
    assert state["sql_source"] == "canned"
    assert "FROM franchisees" in state["sql_query"]
    assert state["sql_parameters"]["organisation_id"] == 1


def test_query_planner_node_uses_text_to_sql_in_llm_mode(monkeypatch):
    monkeypatch.setenv("QUERY_PLANNER_MODE", "llm")
    get_settings.cache_clear()

    class FakeGenerated:
        sql = VALID_SQL.strip()
        parameters = {"organisation_id": 1}
        source = "generated"
        latency_ms = 12.0

    monkeypatch.setattr(
        "app.services.text_to_sql.generate_select",
        lambda question, organisation_id=None, **kwargs: FakeGenerated(),
    )

    try:
        result = query_planner_node(
            {
                "question": "How many franchisees does each coach manage?",
                "organisation_id": 1,
            }
        )
    finally:
        get_settings.cache_clear()

    assert result["error"] is None
    assert result["sql_source"] == "generated"
    assert result["sql_query"].upper().startswith("SELECT")
    assert result["fallback_used"] is False


def test_query_planner_node_falls_back_when_generation_fails(monkeypatch):
    monkeypatch.setenv("QUERY_PLANNER_MODE", "llm")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.text_to_sql.generate_select",
        lambda question, organisation_id=None, **kwargs: None,
    )
    try:
        result = query_planner_node(
            {
                "question": "How many franchisees are there?",
                "organisation_id": 1,
            }
        )
    finally:
        get_settings.cache_clear()

    assert result["error"] is None
    assert result["intent"] == "count_franchisees"
    assert result["fallback_used"] is True
    assert result.get("sql_query") is None
