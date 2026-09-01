from app.services.embedding_service import (
    EmbeddingResult,
    embed_documents_with_fallback,
)


def test_embed_documents_with_fallback_uses_sentence_transformers_when_ollama_fails(monkeypatch):
    calls = []

    def fake_embed(texts, provider="ollama", model_name="nomic-embed-text", **kwargs):
        calls.append(provider)
        if provider == "ollama":
            raise ConnectionError("Ollama is not running")
        return [
            EmbeddingResult(
                embedding=[0.0, 1.0],
                provider=provider,
                model=model_name,
                dimension=2,
            )
            for _ in texts
        ]

    monkeypatch.setattr(
        "app.services.embedding_service.embed_documents",
        fake_embed,
    )

    results = embed_documents_with_fallback(["SmartStart model"])
    assert calls == ["ollama", "sentence-transformers"]
    assert results[0].provider == "sentence-transformers"
    assert results[0].embedding == [0.0, 1.0]


def test_embed_documents_with_fallback_does_not_retry_sentence_transformers(monkeypatch):
    def fake_embed(texts, provider="ollama", **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(
        "app.services.embedding_service.embed_documents",
        fake_embed,
    )
    try:
        embed_documents_with_fallback(
            ["SmartStart model"],
            provider="sentence-transformers",
        )
    except RuntimeError as exc:
        assert "provider down" in str(exc)
    else:
        raise AssertionError("Expected the sentence-transformers error to propagate")
