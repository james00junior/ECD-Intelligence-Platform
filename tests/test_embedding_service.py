from app.services.embedding_service import (
    EmbeddingResult,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    embed_documents,
    embed_text,
    embedding_dimension,
)


def test_embedding_result_contains_dynamic_dimension():
    result = EmbeddingResult(
        embedding=[0.1, 0.2, 0.3],
        provider="test",
        model="test-model",
        dimension=3,
    )

    assert result.dimension == 3
    assert result.dimension == len(result.embedding)


def test_embed_documents_empty_input():
    assert embed_documents([]) == []


def test_embedding_model_has_dynamic_dimension():
    dimension = embedding_dimension(
        provider=DEFAULT_PROVIDER,
        model_name=DEFAULT_MODEL,
    )

    assert dimension > 0


def test_embed_text_returns_embedding_result():
    result = embed_text(
        "Early childhood development is important."
    )

    assert isinstance(result, EmbeddingResult)
    assert isinstance(result.embedding, list)
    assert result.dimension == len(result.embedding)
    assert result.dimension > 0
    assert result.provider
    assert result.model


def test_embedding_is_normalised():
    result = embed_text(
        "Early childhood development is important."
    )

    squared_sum = sum(
        value * value
        for value in result.embedding
    )

    assert abs(squared_sum - 1.0) < 1e-5


def test_embed_documents_returns_multiple_vectors():
    results = embed_documents(
        [
            "ECD franchisees operate learning programmes.",
            "Children participate in early learning activities.",
        ]
    )

    assert len(results) == 2

    for result in results:
        assert isinstance(result, EmbeddingResult)
        assert isinstance(result.embedding, list)
        assert result.dimension == len(result.embedding)
        assert result.dimension > 0


def test_embedding_dimensions_are_consistent():
    results = embed_documents(
        [
            "ECD franchisees operate learning programmes.",
            "Children participate in early learning activities.",
        ]
    )

    dimensions = {
        result.dimension
        for result in results
    }

    assert len(dimensions) == 1


def test_empty_text_is_rejected():
    try:
        embed_text("")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")