from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["version"] == "0.3.0"


def test_agent_count_franchisees():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many franchisees are there?",
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
        "/api/v1/agent/query",
        json={
            "question": "How many active franchisees are there?",
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
        "/api/v1/agent/query",
        json={
            "question": "What is the weather in Johannesburg?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["error"]
        == "No SQL query could be generated for this question."
    )

    assert data["results"] == []


def test_agent_count_franchisees_for_organisation():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many franchisees are there?",
            "organisation_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["intent"] == "count_franchisees"
    assert data["results"]

    assert "franchisee_count" in data["results"][0]


def test_agent_count_franchisees_nonexistent_organisation():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many franchisees are there?",
            "organisation_id": 999999,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["results"] == []


def test_agent_children_scoped_to_organisation():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many children are enrolled?",
            "organisation_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["results"]

    assert "child_count" in data["results"][0]

def test_agent_count_franchisees_nonexistent_organisation():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many franchisees are there?",
            "organisation_id": 999999,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["results"] == []
    assert data["error"] == "Organisation 999999 does not exist."
    assert data["answer"] is None