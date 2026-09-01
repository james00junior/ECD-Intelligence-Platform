from unittest.mock import MagicMock

from app.tools.sql_research_tool import run_sql_research


def test_requires_valid_organisation_scope():
    result = run_sql_research("How many franchisees are there?", None)
    assert result["evidence"] == []
    assert "organisation scope" in result["error"].lower()

    result = run_sql_research("How many franchisees are there?", 0)
    assert result["evidence"] == []
    assert "organisation scope" in result["error"].lower()


def test_rejects_unknown_organisation(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr("app.tools.sql_research_tool.SessionLocal", lambda: db)
    monkeypatch.setattr("app.tools.sql_research_tool.organisation_exists", lambda db, id: False)

    result = run_sql_research("How many franchisees are there?", 9)

    assert result["evidence"] == []
    assert result["error"] == "Organisation 9 does not exist."
    db.close.assert_called_once()


def test_returns_safe_sql_evidence(monkeypatch):
    db = MagicMock()
    agent = MagicMock()
    agent.invoke.return_value = {
        "results": [{"franchisee_count": 4}],
        "sql_query": "SELECT COUNT(*) FROM franchisees WHERE organisation_id = :organisation_id",
        "error": None,
    }
    monkeypatch.setattr("app.tools.sql_research_tool.SessionLocal", lambda: db)
    monkeypatch.setattr("app.tools.sql_research_tool.organisation_exists", lambda db, id: True)
    monkeypatch.setattr("app.tools.sql_research_tool.analytics_agent", agent)

    result = run_sql_research("How many franchisees are there?", 1)

    evidence = result["evidence"][0]
    assert result["error"] is None
    assert evidence["provenance"]["organisation_id"] == 1
    assert evidence["provenance"]["metadata"]["row_count"] == 1
    assert "franchisee_count" in evidence["content"]
    assert agent.invoke.call_args.kwargs == {}
    assert agent.invoke.call_args.args[0]["organisation_id"] == 1
