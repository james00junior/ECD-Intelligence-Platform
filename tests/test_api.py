from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_count_franchisees():
    response = client.post(
        "/agent",
        json={
            "question": "How many franchisees are there?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["intent"] == "count_franchisees"
    assert data["results"]

    assert "franchisee_count" in data["results"][0]


def test_agent_active_franchisees():
    response = client.post(
        "/agent",
        json={
            "question": "How many active franchisees are there?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["intent"] == "active_franchisees"
    assert data["results"]

    assert "active_franchisee_count" in data["results"][0]


def test_agent_unknown_question():
    response = client.post(
        "/agent",
        json={
            "question": "What is the weather in Johannesburg?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["error"]
        == "No SQL query could be generated for this question."
    )

    assert data["results"] == []
