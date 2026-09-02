from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_models_status_does_not_require_ollama(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.models.ollama_client.ollama_reachable",
        lambda: False,
    )
    response = client.get("/api/v1/models/status")
    assert response.status_code == 200
    data = response.json()
    assert data["query_planner_mode"] in {"rule", "llm"}
    assert data["llm_provider"] in {"ollama", "openai"}
    assert data["ollama_reachable"] is False


def test_list_models_includes_catalog_when_ollama_down(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.models.ollama_client.ollama_reachable",
        lambda: False,
    )
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    tags = {item["ollama_tag"] for item in data["recommended"]}
    assert "qwen3.5:0.8b" in tags
    assert data["installed"] == []


def test_pull_rejects_unknown_tag():
    response = client.post("/api/v1/models/pull", json={"tag": "totally-fake:9b"})
    assert response.status_code == 400
