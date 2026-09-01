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
            "question": "How many franchisees are there?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["intent"] == "count_franchisees"
    assert data["route"] == "analytics"
    assert data["results"]

    assert "franchisee_count" in data["results"][0]


def test_agent_active_franchisees():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "question": "How many active franchisees are there?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] is None
    assert data["intent"] == "active_franchisees"
    assert data["route"] == "analytics"
    assert data["results"]

    assert "active_franchisee_count" in data["results"][0]


def test_agent_unknown_question():
    response = client.post(
        "/api/v1/agent/query",
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


def test_list_organisations():
    response = client.get("/api/v1/organisations")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    organisation = data[0]

    assert "id" in organisation
    assert "name" in organisation
    assert "country" in organisation