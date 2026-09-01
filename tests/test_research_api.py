from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_research_endpoint_returns_selected_evidence(monkeypatch):
    db = MagicMock()
    workflow = MagicMock()
    workflow.invoke.return_value = {
        "answer": "Coaching helps. [1]",
        "route": "internal_knowledge",
        "selected_evidence": [{"evidence_id": "document:1"}],
        "citations": [{"reference": 1, "title": "Guide"}],
        "conflicts": [],
        "research_steps": 1,
        "research_attempts": 0,
        "error": None,
    }
    monkeypatch.setattr("app.api.v1.research.SessionLocal", lambda: db)
    monkeypatch.setattr("app.api.v1.research.organisation_exists", lambda db, id: True)
    monkeypatch.setattr("app.api.v1.research.research_workflow", workflow)

    response = client.post("/api/v1/research", json={
        "question": "What does our guide say?", "organisation_id": 1
    })

    assert response.status_code == 200
    assert response.json()["answer"] == "Coaching helps. [1]"
    assert workflow.invoke.call_args.args[0]["organisation_id"] == 1
    db.close.assert_called_once()


def test_research_endpoint_rejects_unknown_organisation(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr("app.api.v1.research.SessionLocal", lambda: db)
    monkeypatch.setattr("app.api.v1.research.organisation_exists", lambda db, id: False)

    response = client.post("/api/v1/research", json={
        "question": "What does our guide say?", "organisation_id": 99
    })

    assert response.status_code == 200
    assert response.json()["error"] == "Organisation 99 does not exist."


def test_chat_interface_and_assets_are_served():
    response = client.get("/")
    stylesheet = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "ECD Intelligence" in response.text
    assert stylesheet.status_code == 200
